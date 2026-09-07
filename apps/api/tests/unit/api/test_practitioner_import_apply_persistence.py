"""Applying a practitioner batch against real PostgreSQL, end to end.

An awaited audit handler is not evidence of an audit record. These drive the
real routes through the deployment's whole chain: route -> outbox row in the
caller's transaction -> worker -> audit_logs, and verify the created
organisations, practitioners, affiliations and per-row provenance ids in the
database, plus the 409 on a second apply.

Run with TEST_DATABASE_URL pointing at local PostgreSQL; skipped without it.
"""

import os
from uuid import uuid4

import pytest
import pytest_asyncio
from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient
from sqlalchemy import select
from sqlalchemy.engine import make_url
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine
from sqlalchemy.pool import NullPool
from sqlalchemy.schema import CreateSchema, DropSchema

from app.api.routes.practitioner_imports import router as imports_router
from app.application.services.outbox_consumers import make_audit_consumer
from app.application.services.outbox_dispatcher import OutboxDispatcher
from app.core.authorization import get_current_user_entity
from app.core.database import get_db
from app.core.exception_handlers import register_exception_handlers
from app.core.security import TokenData, get_current_user
from app.domain.enums import SubscriptionTier, TenantRole, TenantStatus
from app.domain.services.provider_network_calendar import boundary_day
from app.domain.value_objects.core import TenantId, UserId
from app.infrastructure.models.audit_model import AuditLogModel
from app.infrastructure.models.base import Base
from app.infrastructure.models.practitioner_import_model import PractitionerImportRowModel
from app.infrastructure.models.provider_affiliation_model import ProviderAffiliationModel
from app.infrastructure.models.provider_model import ProviderModel
from app.infrastructure.models.provider_organisation_model import ProviderOrganisationModel
from app.infrastructure.models.tenant_model import TenantModel
from app.infrastructure.repositories.audit_repository import AuditRepositoryImpl
from app.infrastructure.repositories.outbox_repository import OutboxRepositoryImpl
from app.shared.utils.datetime import utc_now
from tests.unit.shared.practitioner_workbook_builder import (
    consultant_row,
    partner_row,
    workbook_bytes,
)

TENANT_ID = "tenant-pract-apply"
USER_ID = "user-pract-apply"


@pytest_asyncio.fixture
async def db():
    raw = os.environ.get("TEST_DATABASE_URL")
    if not raw:
        pytest.skip("Set TEST_DATABASE_URL to a local PostgreSQL database")
    url = make_url(raw)
    if url.get_backend_name() != "postgresql":
        pytest.skip("The apply persistence test needs PostgreSQL")
    assert url.host in {"localhost", "127.0.0.1", "::1"}
    schema = "pract_apply_" + uuid4().hex
    admin = create_async_engine(url, poolclass=NullPool)
    async with admin.begin() as connection:
        await connection.execute(CreateSchema(schema))
    engine = create_async_engine(
        url, poolclass=NullPool, connect_args={"server_settings": {"search_path": schema}}
    )
    async with engine.begin() as connection:
        await connection.run_sync(Base.metadata.create_all)
    sessions = async_sessionmaker(engine, expire_on_commit=False)
    async with sessions() as session:
        session.add(
            TenantModel(
                id=TENANT_ID,
                name="Practitioner apply tenant",
                code="papply",
                settings={},
                status=TenantStatus.ACTIVE,
                subscription_tier=SubscriptionTier.FREE,
            )
        )
        await session.commit()
    try:
        yield sessions
    finally:
        await engine.dispose()
        async with admin.begin() as connection:
            await connection.execute(DropSchema(schema, cascade=True))
        await admin.dispose()


def _app(db) -> FastAPI:
    app = FastAPI()
    register_exception_handlers(app)
    app.include_router(imports_router)

    async def override_db():
        async with db() as session:
            yield session

    app.dependency_overrides[get_db] = override_db
    app.dependency_overrides[get_current_user] = lambda: TokenData(
        user_id=USER_ID, tenant_id=TENANT_ID, role=TenantRole.ADMIN.value
    )
    app.dependency_overrides[get_current_user_entity] = lambda: type(
        "U", (), {"id": UserId(USER_ID), "tenant_id": TenantId(TENANT_ID), "role": TenantRole.ADMIN}
    )()
    return app


@pytest_asyncio.fixture
async def api(db):
    transport = ASGITransport(app=_app(db))
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        yield client


def _workbook() -> bytes:
    return workbook_bytes(
        [
            partner_row(name="Jane Doe", company="Safe Places Uganda"),
            partner_row(name="Ann Achen", company="SAFE PLACES UGANDA", email="ann@example.com"),
            partner_row(name="Grace Atim", company="Individual", email=None),
            partner_row(name="Odd Person", profession="Mystery Role"),
        ],
        [consultant_row(name="John Okello", contract="Employee")],
    )


def _upload(content: bytes):
    mime = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    return {"file": ("wb.xlsx", content, mime)}


async def _stage(api, content: bytes) -> str:
    response = await api.post(
        f"/practitioner-imports?tenant_id={TENANT_ID}", files=_upload(content)
    )
    assert response.status_code == 201, response.text
    return response.json()["id"]


async def _rows(db, model) -> list:
    async with db() as session:
        return list((await session.execute(select(model))).scalars().all())


async def _drain(db) -> int:
    async with db() as session:
        dispatcher = OutboxDispatcher(OutboxRepositoryImpl(session))
        dispatcher.register_consumer(make_audit_consumer(AuditRepositoryImpl(session)))
        delivered = await dispatcher.drain_once()
        await session.commit()
        return delivered


class TestApplyPersists:
    async def test_apply_creates_records_audits_them_and_refuses_a_replay(self, api, db):
        batch_id = await _stage(api, _workbook())

        response = await api.post(f"/practitioner-imports/{batch_id}/apply?tenant_id={TENANT_ID}")
        assert response.status_code == 200, response.text
        body = response.json()
        assert body["created_providers"] == 3
        assert body["created_organisations"] == 1
        assert body["reused_organisations"] == 0
        assert body["created_affiliations"] == 2
        assert body["failed"] == 0
        assert body["not_applicable"] == 2
        assert body["batch"]["status"] == "Applied"

        providers = await _rows(db, ProviderModel)
        assert {p.display_name for p in providers} == {"Jane Doe", "Ann Achen", "Grace Atim"}
        for provider in providers:
            assert provider.status == "Pending"
            assert provider.provider_profile["tier"] is None
            assert provider.provider_profile["region"] is None
            assert provider.provider_profile["panel_status"] == "Pending"
            assert provider.provider_profile["accreditation_status"] == "Pending"

        organisations = await _rows(db, ProviderOrganisationModel)
        assert len(organisations) == 1
        assert organisations[0].name == "Safe Places Uganda"
        assert organisations[0].approval_status == "Pending"

        affiliations = await _rows(db, ProviderAffiliationModel)
        assert len(affiliations) == 2
        today = boundary_day(utc_now())
        assert all(a.valid_from == today and a.valid_until is None for a in affiliations)
        assert all(a.organisation_id == organisations[0].id for a in affiliations)

        applied_rows = [
            r for r in await _rows(db, PractitionerImportRowModel) if r.imported_provider_id
        ]
        assert len(applied_rows) == 3
        assert {r.imported_provider_id for r in applied_rows} == {p.id for p in providers}

        # Staged event, then 1 organisation + 3 providers + 2 affiliations + batch applied.
        assert await _drain(db) == 8
        logs = await _rows(db, AuditLogModel)
        events = {log.extra_metadata["event_type"] for log in logs}
        assert events == {
            "PractitionerImportBatchStaged",
            "PractitionerImportBatchApplied",
            "ProviderOrganisationCreated",
            "ProviderCreated",
            "ProviderAffiliationCreated",
        }
        assert all(log.tenant_id == TENANT_ID and log.user_id == USER_ID for log in logs)

        replay = await api.post(f"/practitioner-imports/{batch_id}/apply?tenant_id={TENANT_ID}")
        assert replay.status_code == 409, replay.text
        assert len(await _rows(db, ProviderModel)) == 3

    async def test_an_existing_organisation_is_reused_never_duplicated(self, api, db):
        first = await _stage(api, _workbook())
        await api.post(f"/practitioner-imports/{first}/apply?tenant_id={TENANT_ID}")

        second = await _stage(
            api,
            workbook_bytes([partner_row(name="New Person", company="safe places uganda")]),
        )
        response = await api.post(f"/practitioner-imports/{second}/apply?tenant_id={TENANT_ID}")
        assert response.status_code == 200, response.text
        assert response.json()["created_organisations"] == 0
        assert response.json()["reused_organisations"] == 1
        assert len(await _rows(db, ProviderOrganisationModel)) == 1

    async def test_a_batch_with_no_accepted_rows_applies_and_creates_nothing(self, api, db):
        batch_id = await _stage(
            api,
            workbook_bytes([partner_row(name="Odd Person", profession="Mystery Role")]),
        )
        response = await api.post(f"/practitioner-imports/{batch_id}/apply?tenant_id={TENANT_ID}")
        assert response.status_code == 200, response.text
        assert response.json()["created_providers"] == 0
        assert response.json()["batch"]["status"] == "Applied"
        assert await _rows(db, ProviderModel) == []
