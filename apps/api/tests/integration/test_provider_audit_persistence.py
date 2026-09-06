"""Provider mutations reach audit_logs, and a failure leaves neither behind.

An awaited audit handler is not evidence of an audit record. These drive the
real routes against real PostgreSQL through the whole chain the deployment
uses: route -> outbox row in the caller's transaction -> worker -> audit_logs.
They also prove the two negative cases, that a forbidden write saves nothing
and that a failure after the audit call rolls back the state change and the
outbox row together.

Run with MEMBER_TEST_DATABASE_URL pointing at local PostgreSQL.
"""

from uuid import uuid4

import pytest_asyncio
from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient
from sqlalchemy import select
from sqlalchemy.engine import make_url
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine
from sqlalchemy.pool import NullPool
from sqlalchemy.schema import CreateSchema, DropSchema

from app.api.routes.providers import router as providers_router
from app.application.services.outbox_consumers import make_audit_consumer
from app.application.services.outbox_dispatcher import OutboxDispatcher
from app.core.authorization import get_current_user_entity
from app.core.database import get_db
from app.core.exception_handlers import register_exception_handlers
from app.core.security import TokenData, get_current_user
from app.domain.enums import (
    AccreditationStatus,
    BaseStatus,
    PanelStatus,
    ProviderIdentityProvenance,
    ProviderTier,
    SubscriptionTier,
    TenantRole,
    TenantStatus,
    UgandaRegion,
)
from app.domain.value_objects.core import TenantId, UserId
from app.infrastructure.models.audit_model import AuditLogModel
from app.infrastructure.models.base import Base
from app.infrastructure.models.outbox_model import OutboxEventModel
from app.infrastructure.models.provider_model import ProviderModel
from app.infrastructure.models.tenant_model import TenantModel
from app.infrastructure.repositories.audit_repository import AuditRepositoryImpl
from app.infrastructure.repositories.outbox_repository import OutboxRepositoryImpl
from app.shared.utils.datetime import utc_now
from tests.integration._database_url import require_local_database

TENANT_ID = "tenant-provider-audit"
USER_ID = "user-provider-audit"
PROVIDER_ID = "provider-audit-1"


def _profile() -> dict:
    return {
        "tier": ProviderTier.T1.value,
        "region": UgandaRegion.CENTRAL.value,
        "accreditation_status": AccreditationStatus.ACCREDITED.value,
        "panel_status": PanelStatus.ACTIVE.value,
        "accreditation_authority": "UCC",
        "accreditation_expiry": None,
        "specialties": [],
        "bio": None,
    }


@pytest_asyncio.fixture
async def db():
    url = make_url(require_local_database("MEMBER_TEST_DATABASE_URL"))
    schema = "provider_audit_" + uuid4().hex
    admin = create_async_engine(url, poolclass=NullPool)
    async with admin.begin() as connection:
        await connection.execute(CreateSchema(schema))
    engine = create_async_engine(
        url, poolclass=NullPool, connect_args={"server_settings": {"search_path": schema}}
    )
    async with engine.begin() as connection:
        await connection.run_sync(Base.metadata.create_all)
    sessions = async_sessionmaker(engine, expire_on_commit=False)

    now = utc_now()
    async with sessions() as session:
        session.add(
            TenantModel(
                id=TENANT_ID,
                name="Provider audit tenant",
                code="pauda",
                settings={},
                status=TenantStatus.ACTIVE,
                subscription_tier=SubscriptionTier.FREE,
            )
        )
        await session.commit()
    async with sessions() as session:
        session.add(
            ProviderModel(
                id=PROVIDER_ID,
                tenant_id=TENANT_ID,
                user_id=None,
                display_name="Amina Okello",
                contact_email="amina@example.test",
                contact_phone=None,
                identity_provenance=ProviderIdentityProvenance.OWNED,
                status=BaseStatus.ACTIVE,
                license_info=None,
                provider_profile=_profile(),
                created_at=now,
                updated_at=now,
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


def _app(db, *, role: TenantRole = TenantRole.ADMIN) -> FastAPI:
    app = FastAPI()
    register_exception_handlers(app)
    app.include_router(providers_router)

    async def override_db():
        async with db() as session:
            yield session

    app.dependency_overrides[get_db] = override_db
    app.dependency_overrides[get_current_user] = lambda: TokenData(
        user_id=USER_ID, tenant_id=TENANT_ID, role=role.value
    )
    app.dependency_overrides[get_current_user_entity] = lambda: type(
        "U", (), {"id": UserId(USER_ID), "tenant_id": TenantId(TENANT_ID), "role": role}
    )()
    return app


@pytest_asyncio.fixture
async def api(db):
    transport = ASGITransport(app=_app(db))
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        yield client


async def _drain(db) -> int:
    async with db() as session:
        dispatcher = OutboxDispatcher(OutboxRepositoryImpl(session))
        dispatcher.register_consumer(make_audit_consumer(AuditRepositoryImpl(session)))
        delivered = await dispatcher.drain_once()
        await session.commit()
        return delivered


async def _rows(db, model) -> list:
    async with db() as session:
        return list((await session.execute(select(model))).scalars().all())


async def _provider_row(db) -> ProviderModel:
    async with db() as session:
        return (
            await session.execute(select(ProviderModel).where(ProviderModel.id == PROVIDER_ID))
        ).scalar_one()


class TestAuditRecordsPersist:
    async def test_a_tier_change_reaches_audit_logs(self, api, db):
        response = await api.patch(
            f"/providers/{PROVIDER_ID}/tier",
            json={"tier": "T3", "reason": "Annual panel review"},
            headers={"user-agent": "audit-test", "x-forwarded-for": "203.0.113.9"},
        )
        assert response.status_code == 200, response.text

        assert (await _provider_row(db)).provider_profile["tier"] == "T3"
        assert len(await _rows(db, OutboxEventModel)) == 1
        assert await _rows(db, AuditLogModel) == []

        assert await _drain(db) == 1
        logs = await _rows(db, AuditLogModel)
        assert len(logs) == 1
        assert logs[0].tenant_id == TENANT_ID
        assert logs[0].user_id == USER_ID
        assert logs[0].resource_id == PROVIDER_ID
        assert logs[0].ip_address == "203.0.113.9"

    async def test_creation_reaches_audit_logs(self, api, db):
        response = await api.post(
            f"/providers?tenant_id={TENANT_ID}",
            json={"display_name": "New Practitioner", "tier": "T2", "region": "Eastern"},
        )
        assert response.status_code == 201, response.text
        assert await _drain(db) == 1
        assert len(await _rows(db, AuditLogModel)) == 1

    async def test_a_general_patch_reaches_audit_logs(self, api, db):
        response = await api.patch(f"/providers/{PROVIDER_ID}", json={"phone": "+256700000000"})
        assert response.status_code == 200, response.text
        assert (await _provider_row(db)).contact_phone == "+256700000000"
        assert await _drain(db) == 1
        assert len(await _rows(db, AuditLogModel)) == 1

    async def test_an_unchanged_command_writes_neither_state_nor_audit(self, api, db):
        before = (await _provider_row(db)).updated_at
        response = await api.patch(
            f"/providers/{PROVIDER_ID}/tier", json={"tier": "T1", "reason": "reaffirm"}
        )
        assert response.status_code == 200, response.text
        assert await _rows(db, OutboxEventModel) == []
        assert (await _provider_row(db)).updated_at == before


class TestForbiddenWritesSaveNothing:
    async def test_a_viewer_tier_change_is_refused_and_persists_nothing(self, db):
        transport = ASGITransport(app=_app(db, role=TenantRole.VIEWER))
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.patch(
                f"/providers/{PROVIDER_ID}/tier", json={"tier": "T3", "reason": "nope"}
            )
        assert response.status_code == 403, response.text
        assert (await _provider_row(db)).provider_profile["tier"] == "T1"
        assert await _rows(db, OutboxEventModel) == []

    async def test_a_non_admin_lifecycle_command_persists_nothing(self, db):
        transport = ASGITransport(app=_app(db, role=TenantRole.USER))
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.patch(
                f"/providers/{PROVIDER_ID}/panel-status",
                json={"panel_status": "Removed", "reason": "nope"},
            )
        assert response.status_code == 403, response.text
        assert (await _provider_row(db)).provider_profile["panel_status"] == "Active"
        assert await _rows(db, OutboxEventModel) == []

    async def test_a_protected_field_in_a_general_patch_persists_nothing(self, api, db):
        response = await api.patch(f"/providers/{PROVIDER_ID}", json={"tier": "T3"})
        assert response.status_code == 422, response.text
        assert (await _provider_row(db)).provider_profile["tier"] == "T1"
        assert await _rows(db, OutboxEventModel) == []


class TestFailureRollsBackBoth:
    async def test_a_failure_after_the_audit_call_leaves_no_state_and_no_outbox_row(self, db):
        """The state change and its audit row commit together or not at all.

        The failure is injected after the route has changed the provider and
        enqueued the outbox row, in the commit itself, which is the window
        where a non-transactional audit would leave a record of a change that
        never happened.
        """
        app = _app(db)
        failed = {"raised": False}

        async def failing_db():
            async with db() as session:
                original_commit = session.commit

                async def commit():
                    failed["raised"] = True
                    raise RuntimeError("commit failed after the audit enqueue")

                session.commit = commit
                try:
                    yield session
                finally:
                    session.commit = original_commit

        app.dependency_overrides[get_db] = failing_db
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.patch(
                f"/providers/{PROVIDER_ID}/tier",
                json={"tier": "T3", "reason": "will not survive"},
            )

        assert failed["raised"] is True
        assert response.status_code == 500, response.text
        assert (await _provider_row(db)).provider_profile["tier"] == "T1"
        assert await _rows(db, OutboxEventModel) == []
        assert await _rows(db, AuditLogModel) == []
