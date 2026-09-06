"""Run with MEMBER_TEST_DATABASE_URL pointing at local PostgreSQL."""

import asyncio
import csv
import io
import os
from types import SimpleNamespace
from unittest.mock import AsyncMock
from uuid import uuid4

import pytest
import pytest_asyncio
from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient
from sqlalchemy import func, select, text
from sqlalchemy.engine import make_url
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine
from sqlalchemy.pool import NullPool
from sqlalchemy.schema import CreateSchema, DropSchema

from app.api.dependencies import get_client_repository, get_outbox_repository, get_user_repository
from app.api.routes.members import router
from app.core.database import get_db
from app.core.exception_handlers import register_exception_handlers
from app.core.security import TokenData, get_current_user
from app.domain.enums import SubscriptionTier, TenantRole, TenantStatus
from app.domain.value_objects.core import TenantId, UserId
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
            await connection.execute(text("CREATE TABLE users (id varchar(25) PRIMARY KEY)"))
            await connection.run_sync(lambda sync: Base.metadata.create_all(sync, tables=tables))
            for ddl in (
                "CREATE TABLE service_sessions (id varchar(25) PRIMARY KEY, tenant_id varchar(25) NOT NULL, member_id varchar(25) NOT NULL REFERENCES eligible_members(id), updated_at timestamptz)",
                "CREATE TABLE cases (id varchar(25) PRIMARY KEY, tenant_id varchar(25) NOT NULL, clinical_subject_id varchar(25) NOT NULL, updated_at timestamptz)",
                "CREATE TABLE clinical_notes (id varchar(25) PRIMARY KEY, tenant_id varchar(25) NOT NULL, clinical_subject_id varchar(25) NOT NULL, updated_at timestamptz)",
                "CREATE TABLE authorizations (id varchar(25) PRIMARY KEY, tenant_id varchar(25) NOT NULL, clinical_subject_id varchar(25) NOT NULL, updated_at timestamptz)",
            ):
                await connection.execute(text(ddl))
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
    users = AsyncMock()
    users.get_by_id.return_value = SimpleNamespace(
        id=UserId("u1"), tenant_id=TenantId("t1"), role=TenantRole.ADMIN, deleted_at=None
    )
    app.dependency_overrides[get_db] = session_dependency
    app.dependency_overrides[get_current_user] = lambda: TokenData(
        user_id="u1", tenant_id="t1", role="Admin"
    )
    app.dependency_overrides[get_client_repository] = lambda: clients
    app.dependency_overrides[get_user_repository] = lambda: users
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as http:
        yield http, app


async def create_member(http, employer_member_id="HR-1", display_label="Test member"):
    response = await http.post(
        "/members",
        json={
            "client_id": "c1",
            "employer_member_id": employer_member_id,
            "display_label": display_label,
            "relation": "Employee",
        },
    )
    assert response.status_code == 201, response.text
    return response.json()["id"]


async def test_reviewed_merge_moves_references_and_deletes_only_the_source(
    member_http, isolated_members_db
):
    http, _ = member_http
    target_id = await create_member(http, "HR-1", "Member to keep")
    source_id = await create_member(http, "HR-2", "Duplicate member")
    child = await http.post(
        "/members",
        json={
            "client_id": "c1",
            "employer_member_id": "HR-3",
            "display_label": "Child",
            "relation": "Child",
            "primary_employee_member_id": source_id,
        },
    )
    assert child.status_code == 201, child.text
    contact = await http.post(
        f"/members/{source_id}/next-of-kin",
        json={"name": "Contact", "relationship": "Sibling", "phone": "123"},
    )
    assert contact.status_code == 201, contact.text

    async with isolated_members_db() as session:
        links = (
            await session.execute(
                select(
                    EligibleMemberClinicalLinkModel.member_id,
                    EligibleMemberClinicalLinkModel.subject_id,
                ).where(EligibleMemberClinicalLinkModel.member_id.in_([source_id, target_id]))
            )
        ).all()
        subjects = dict(links)
        await session.execute(
            text(
                "INSERT INTO service_sessions (id, tenant_id, member_id) "
                "VALUES ('session-1', 't1', :member_id)"
            ),
            {"member_id": source_id},
        )
        for table in ("cases", "clinical_notes", "authorizations"):
            await session.execute(
                text(
                    f"INSERT INTO {table} (id, tenant_id, clinical_subject_id) "
                    "VALUES (:id, 't1', :subject_id), (:foreign_id, 't2', :subject_id)"
                ),
                {
                    "id": f"{table}-1",
                    "foreign_id": f"foreign-{table}",
                    "subject_id": subjects[source_id],
                },
            )
        await session.commit()

    merged = await http.post(f"/members/{target_id}/merge", json={"source_member_id": source_id})
    assert merged.status_code == 200, merged.text
    assert merged.json()["transferred"] == {
        "sessions": 1,
        "beneficiaries": 1,
        "next_of_kin": 1,
        "cases": 1,
        "clinical_notes": 1,
        "authorizations": 1,
        "account_links": 0,
    }
    assert (await http.get(f"/members/{source_id}")).status_code == 404

    async with isolated_members_db() as session:
        child_row = await session.get(EligibleMemberModel, child.json()["id"])
        assert child_row.primary_employee_member_id == target_id
        assert (
            await session.get(MemberNextOfKinModel, contact.json()["id"])
        ).member_id == target_id
        assert (
            await session.scalar(
                text("SELECT member_id FROM service_sessions WHERE id = 'session-1'")
            )
            == target_id
        )
        for table in ("cases", "clinical_notes", "authorizations"):
            assert (
                await session.scalar(
                    text(f"SELECT clinical_subject_id FROM {table} WHERE id = :id"),
                    {"id": f"{table}-1"},
                )
                == subjects[target_id]
            )
            assert (
                await session.scalar(
                    text(f"SELECT clinical_subject_id FROM {table} WHERE id = :id"),
                    {"id": f"foreign-{table}"},
                )
                == subjects[source_id]
            )
        assert await session.get(ClinicalSubjectModel, subjects[source_id]) is None


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


async def test_patching_one_identity_number_preserves_the_others(member_http, isolated_members_db):
    """PATCH was never exercised for these columns; create alone proves nothing here."""
    http, _ = member_http
    created = await http.post(
        "/members",
        json={
            "client_id": "c1",
            "display_label": "Amina",
            "relation": "Employee",
            "staff_number": "EMP-9",
            "national_id": "CM12345",
        },
    )
    assert created.status_code == 201, created.text
    member_id = created.json()["id"]

    changed = await http.patch(
        f"/members/{member_id}",
        json={"national_id": "CM99999", "passport_number": "B0987654"},
    )

    assert changed.status_code == 200, changed.text
    body = changed.json()
    assert body["national_id"] == "CM99999"
    assert body["passport_number"] == "B0987654"
    # The untouched field must survive the partial update's merge.
    assert body["staff_number"] == "EMP-9"
    async with isolated_members_db() as session:
        row = await session.get(EligibleMemberModel, member_id)
        assert row.national_id == "CM99999"
        assert row.passport_number == "B0987654"
        assert row.staff_number == "EMP-9"


async def test_patching_another_field_keeps_the_issued_member_code(member_http):
    """MemberUpdate leaves the code out, so the merge must fall back to the stored one."""
    http, _ = member_http
    created = await http.post(
        "/members",
        json={"client_id": "c1", "display_label": "Amina", "relation": "Employee"},
    )
    assert created.status_code == 201, created.text
    member_id = created.json()["id"]
    assert created.json()["employer_member_id"] == "ACM-001"

    changed = await http.patch(f"/members/{member_id}", json={"phone": "+256700000000"})

    assert changed.status_code == 200, changed.text
    assert changed.json()["employer_member_id"] == "ACM-001"


async def test_export_csv_carries_the_identity_columns(member_http):
    http, _ = member_http
    created = await http.post(
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
    assert created.status_code == 201, created.text

    response = await http.get("/members/export")

    assert response.status_code == 200, response.text
    rows = list(csv.DictReader(io.StringIO(response.text)))
    assert rows[0]["staff_number"] == "EMP-9"
    assert rows[0]["national_id"] == "CM12345"
    assert rows[0]["passport_number"] == "B0987654"
    assert rows[0]["employer_member_id"] == "ACM-001"


async def test_concurrent_auto_issue_does_not_produce_duplicate_codes(
    member_http, isolated_members_db
):
    """Two enrolments in flight at once against the real unique constraint.

    Documents the actual behaviour: the in-request retry only sees committed
    rows, so this is where the guarantee has to come from the database.
    """
    http, _ = member_http
    payload = {"client_id": "c1", "display_label": "Concurrent", "relation": "Employee"}

    responses = await asyncio.gather(
        http.post("/members", json=payload),
        http.post("/members", json=payload),
        return_exceptions=True,
    )

    statuses = sorted(r.status_code for r in responses if not isinstance(r, BaseException))
    # The loser must be told it conflicted, never handed a 500.
    assert 500 not in statuses, statuses
    created = [r for r in responses if not isinstance(r, BaseException) and r.status_code == 201]
    async with isolated_members_db() as session:
        stored = list(await session.scalars(select(EligibleMemberModel.employer_member_id)))

    # Whatever the outcome, the roster must never end up with a duplicate code.
    assert len(stored) == len(set(stored)), stored
    assert len(stored) == len(created)
