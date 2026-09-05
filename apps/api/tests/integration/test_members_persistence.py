"""Run with MEMBER_TEST_DATABASE_URL pointing at local PostgreSQL."""

import asyncio
import os
from types import SimpleNamespace
from unittest.mock import AsyncMock
from uuid import uuid4

import pytest
import pytest_asyncio
from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient
from sqlalchemy import func, select
from sqlalchemy.engine import make_url
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine
from sqlalchemy.pool import NullPool
from sqlalchemy.schema import CreateSchema, DropSchema

from app.api.dependencies import get_client_repository, get_outbox_repository
from app.api.routes.members import router
from app.core.database import get_db
from app.core.exception_handlers import register_exception_handlers
from app.core.security import TokenData, get_current_user
from app.domain.enums import SubscriptionTier, TenantStatus
from app.domain.value_objects.core import TenantId
from app.infrastructure.models.base import Base
from app.infrastructure.models.eligible_member_model import (
    ClinicalSubjectModel,
    EligibleMemberClinicalLinkModel,
    EligibleMemberModel,
)
from app.infrastructure.models.member_next_of_kin_model import MemberNextOfKinModel
from app.infrastructure.models.outbox_model import OutboxEventModel
from app.infrastructure.models.tenant_model import TenantModel


@pytest_asyncio.fixture
async def isolated_members_db():
    raw_url = os.environ.get("MEMBER_TEST_DATABASE_URL")
    if not raw_url:
        pytest.skip("Set MEMBER_TEST_DATABASE_URL to local PostgreSQL")
    url = make_url(raw_url)
    if url.host not in {"localhost", "127.0.0.1", "::1"}:
        pytest.fail("Member persistence tests require local PostgreSQL")
    schema = "members_test_" + uuid4().hex
    admin = create_async_engine(url, poolclass=NullPool)
    async with admin.begin() as connection:
        await connection.execute(CreateSchema(schema))
    engine = create_async_engine(
        url, poolclass=NullPool, connect_args={"server_settings": {"search_path": schema}}
    )
    sessions = async_sessionmaker(engine, expire_on_commit=False)
    tables = [
        Base.metadata.tables[model.__tablename__]
        for model in (
            TenantModel,
            EligibleMemberModel,
            ClinicalSubjectModel,
            EligibleMemberClinicalLinkModel,
            MemberNextOfKinModel,
            OutboxEventModel,
        )
    ]
    try:
        async with engine.begin() as connection:
            await connection.run_sync(lambda sync: Base.metadata.create_all(sync, tables=tables))
        async with sessions() as session:
            session.add(
                TenantModel(
                    id="t1",
                    name="Test",
                    code="TEST",
                    settings={},
                    status=TenantStatus.ACTIVE,
                    subscription_tier=SubscriptionTier.FREE,
                )
            )
            await session.commit()
        yield sessions
    finally:
        await engine.dispose()
        async with admin.begin() as connection:
            await connection.execute(DropSchema(schema, cascade=True))
        await admin.dispose()


@pytest_asyncio.fixture
async def member_http(isolated_members_db):
    app = FastAPI()
    app.include_router(router)
    register_exception_handlers(app)

    async def session_dependency():
        async with isolated_members_db() as session:
            yield session

    clients = AsyncMock()
    clients.get_by_id.return_value = SimpleNamespace(
        tenant_id=TenantId("t1"), name="Acme", code="ACM"
    )
    app.dependency_overrides[get_db] = session_dependency
    app.dependency_overrides[get_current_user] = lambda: TokenData(
        user_id="u1", tenant_id="t1", role="Admin"
    )
    app.dependency_overrides[get_client_repository] = lambda: clients
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as http:
        yield http, app


async def create_member(http):
    response = await http.post(
        "/members",
        json={
            "client_id": "c1",
            "employer_member_id": "HR-1",
            "display_label": "Test member",
            "relation": "Employee",
        },
    )
    assert response.status_code == 201, response.text
    return response.json()["id"]


async def test_success_survives_request_session_and_preserves_clinical_link(
    member_http, isolated_members_db
):
    http, _ = member_http
    member_id = await create_member(http)
    response = await http.patch(f"/members/{member_id}", json={"phone": "123"})
    assert response.status_code == 200, response.text
    async with isolated_members_db() as session:
        row = await session.get(EligibleMemberModel, member_id)
        assert row.phone == "123"
        assert await session.scalar(select(func.count()).select_from(ClinicalSubjectModel)) == 1
        assert (
            await session.scalar(select(func.count()).select_from(EligibleMemberClinicalLinkModel))
            == 1
        )
        assert await session.scalar(select(func.count()).select_from(OutboxEventModel)) == 2


async def test_failed_audit_does_not_persist_member_change(member_http, isolated_members_db):
    http, app = member_http
    member_id = await create_member(http)
    outbox = AsyncMock()
    outbox.enqueue.side_effect = RuntimeError("audit unavailable")
    app.dependency_overrides[get_outbox_repository] = lambda: outbox
    response = await http.patch(f"/members/{member_id}", json={"phone": "123"})
    assert response.status_code == 500
    async with isolated_members_db() as session:
        row = await session.get(EligibleMemberModel, member_id)
        assert row.phone is None
        assert await session.scalar(select(func.count()).select_from(OutboxEventModel)) == 1


async def test_concurrent_primary_contacts_have_one_primary(member_http, isolated_members_db):
    http, _ = member_http
    member_id = await create_member(http)
    responses = await asyncio.gather(
        *[
            http.post(
                f"/members/{member_id}/next-of-kin",
                json={"name": name, "relationship": "Other", "phone": "123", "is_primary": True},
            )
            for name in ("First contact", "Second contact")
        ]
    )
    assert [response.status_code for response in responses] == [201, 201]
    async with isolated_members_db() as session:
        contacts = (await session.scalars(select(MemberNextOfKinModel))).all()
        assert len(contacts) == 2
        assert sum(contact.is_primary for contact in contacts) == 1


async def test_repository_filters_and_tenant_isolation(member_http, isolated_members_db):
    http, _ = member_http
    primary_id = await create_member(http)
    response = await http.post(
        "/members",
        json={
            "client_id": "c1",
            "employer_member_id": "HR-2",
            "display_label": "Child member",
            "relation": "Child",
            "primary_employee_member_id": primary_id,
        },
    )
    assert response.status_code == 201, response.text
    async with isolated_members_db() as session:
        session.add(
            TenantModel(
                id="t2",
                name="Other tenant",
                code="OTHER",
                settings={},
                status=TenantStatus.ACTIVE,
                subscription_tier=SubscriptionTier.FREE,
            )
        )
        await session.flush()
        session.add(
            EligibleMemberModel(
                id="foreign",
                tenant_id="t2",
                client_id="c1",
                employer_member_id="HR-3",
                display_label="Private name",
                relation="Child",
                status="Active",
                primary_employee_member_id=primary_id,
            )
        )
        await session.commit()
    listed = await http.get(
        "/members", params={"client_id": "c1", "relation": "Employee", "sort_by": "relation"}
    )
    assert listed.status_code == 200, listed.text
    assert listed.json()["total"] == 1
    assert listed.json()["items"][0]["id"] == primary_id
    beneficiaries = await http.get(f"/members/{primary_id}/beneficiaries")
    assert len(beneficiaries.json()) == 1
    assert beneficiaries.json()[0]["display_label"] == "Child member"
    assert (await http.get("/members/foreign")).status_code == 404


async def test_member_codes_are_issued_in_sequence_against_postgresql(
    member_http, isolated_members_db
):
    """The real HTTP path, real repository, real unique constraint.

    Mocked route tests cannot show that the sequence keeps counting across
    requests, nor that the per-client unique index tolerates it.
    """
    http, _ = member_http
    issued = []
    for _ in range(3):
        response = await http.post(
            "/members",
            json={"client_id": "c1", "display_label": "Auto member", "relation": "Employee"},
        )
        assert response.status_code == 201, response.text
        issued.append(response.json()["employer_member_id"])

    assert issued == ["ACM-001", "ACM-002", "ACM-003"]

    async with isolated_members_db() as session:
        stored = await session.scalars(select(EligibleMemberModel.employer_member_id))
        assert sorted(stored) == ["ACM-001", "ACM-002", "ACM-003"]


async def test_hand_written_codes_do_not_get_reissued(member_http):
    """An imported roster already using the prefix must not collide."""
    http, _ = member_http
    seeded = await http.post(
        "/members",
        json={
            "client_id": "c1",
            "employer_member_id": "ACM-007",
            "display_label": "Imported",
            "relation": "Employee",
        },
    )
    assert seeded.status_code == 201, seeded.text

    response = await http.post(
        "/members",
        json={"client_id": "c1", "display_label": "Next", "relation": "Employee"},
    )

    assert response.status_code == 201, response.text
    assert response.json()["employer_member_id"] == "ACM-008"


async def test_identity_numbers_round_trip_through_postgresql(member_http, isolated_members_db):
    http, _ = member_http
    response = await http.post(
        "/members",
        json={
            "client_id": "c1",
            "display_label": "Amina",
            "relation": "Employee",
            "staff_number": "EMP-9",
            "national_id": "CM12345",
            "passport_number": "B0987654",
        },
    )
    assert response.status_code == 201, response.text
    member_id = response.json()["id"]

    async with isolated_members_db() as session:
        row = await session.get(EligibleMemberModel, member_id)
        assert (row.staff_number, row.national_id, row.passport_number) == (
            "EMP-9",
            "CM12345",
            "B0987654",
        )

    listed = await http.get("/members")
    assert listed.status_code == 200, listed.text
    item = listed.json()["items"][0]
    assert item["national_id"] == "CM12345"
    assert item["client_name"] == "Acme"


async def test_duplicate_member_code_is_rejected_not_500(member_http):
    http, _ = member_http
    payload = {
        "client_id": "c1",
        "employer_member_id": "ACM-001",
        "display_label": "First",
        "relation": "Employee",
    }
    assert (await http.post("/members", json=payload)).status_code == 201

    duplicate = await http.post("/members", json={**payload, "display_label": "Second"})

    assert duplicate.status_code == 409, duplicate.text
