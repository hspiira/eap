"""Engagement structural mutations reach audit_logs.

AUD-01 recorded that adding a deliverable, changing its status and logging
hours injected an audit handler and returned without calling it. An awaited
handler would not be evidence either: these drive the real routes against real
PostgreSQL through the chain the deployment uses, route -> outbox row in the
caller's transaction -> worker -> audit_logs, and assert the persisted row.

Run with TEST_DATABASE_URL pointing at local PostgreSQL.
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

from app.api.routes.engagements import router as engagements_router
from app.application.services.outbox_consumers import make_audit_consumer
from app.application.services.outbox_dispatcher import OutboxDispatcher
from app.core.database import get_db
from app.core.exception_handlers import register_exception_handlers
from app.core.security import TokenData, get_current_user
from app.domain.enums import (
    DeliverableStatus,
    EngagementStatus,
    SubscriptionTier,
    TenantRole,
    TenantStatus,
)
from app.infrastructure.models.audit_model import AuditLogModel
from app.infrastructure.models.base import Base
from app.infrastructure.models.engagement_model import EngagementModel
from app.infrastructure.models.outbox_model import OutboxEventModel
from app.infrastructure.models.tenant_model import TenantModel
from app.infrastructure.repositories.audit_repository import AuditRepositoryImpl
from app.infrastructure.repositories.outbox_repository import OutboxRepositoryImpl
from app.shared.utils.datetime import utc_now
from tests.integration._database_url import require_local_database

TENANT_ID = "tenant-engagement-audit"
USER_ID = "user-engagement-audit"
ENGAGEMENT_ID = "engagement-audit-1"


@pytest_asyncio.fixture
async def db():
    url = make_url(require_local_database("TEST_DATABASE_URL"))
    schema = "engagement_audit_" + uuid4().hex
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
                name="Engagement audit tenant",
                code="engau",
                settings={},
                status=TenantStatus.ACTIVE,
                subscription_tier=SubscriptionTier.FREE,
            )
        )
        await session.commit()
    async with sessions() as session:
        session.add(
            EngagementModel(
                id=ENGAGEMENT_ID,
                tenant_id=TENANT_ID,
                client_id="client-audit-1",
                name="Policy refresh",
                description=None,
                status=EngagementStatus.ACTIVE,
                period_start=None,
                period_end=None,
                deliverables=[],
                hours_log=[],
                created_by=USER_ID,
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
    app.include_router(engagements_router)

    async def override_db():
        async with db() as session:
            yield session

    app.dependency_overrides[get_db] = override_db
    app.dependency_overrides[get_current_user] = lambda: TokenData(
        user_id=USER_ID, tenant_id=TENANT_ID, role=role.value
    )
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


async def _audit_logs(db) -> list[AuditLogModel]:
    async with db() as session:
        stmt = select(AuditLogModel).order_by(AuditLogModel.occurred_at)
        return list((await session.execute(stmt)).scalars().all())


def _event(log: AuditLogModel) -> dict:
    return log.extra_metadata["event_data"]


async def _engagement_row(db) -> EngagementModel:
    async with db() as session:
        return (
            await session.execute(
                select(EngagementModel).where(EngagementModel.id == ENGAGEMENT_ID)
            )
        ).scalar_one()


async def _add_deliverable(api, title: str = "Policy draft v1") -> str:
    response = await api.post(
        f"/engagements/{ENGAGEMENT_ID}/deliverables",
        json={"title": title, "description": None, "due_date": None},
        headers={"user-agent": "audit-test", "x-forwarded-for": "203.0.113.9"},
    )
    assert response.status_code == 201, response.text
    return response.json()["id"]


class TestStructuralMutationsReachAuditLogs:
    async def test_adding_a_deliverable_reaches_audit_logs(self, api, db):
        deliverable_id = await _add_deliverable(api)

        row = await _engagement_row(db)
        assert [d["id"] for d in row.deliverables] == [deliverable_id]
        assert len(await _rows(db, OutboxEventModel)) == 1
        assert await _rows(db, AuditLogModel) == []

        assert await _drain(db) == 1
        logs = await _audit_logs(db)
        assert len(logs) == 1
        assert logs[0].extra_metadata["event_type"] == "DeliverableAdded"
        assert _event(logs[0])["deliverable_id"] == deliverable_id
        assert logs[0].tenant_id == TENANT_ID
        assert logs[0].user_id == USER_ID
        assert logs[0].resource_type == "Engagement"
        assert logs[0].resource_id == ENGAGEMENT_ID
        assert logs[0].ip_address == "203.0.113.9"

    async def test_a_deliverable_status_change_reaches_audit_logs(self, api, db):
        deliverable_id = await _add_deliverable(api)
        assert await _drain(db) == 1

        response = await api.patch(
            f"/engagements/{ENGAGEMENT_ID}/deliverables/{deliverable_id}",
            json={"status": DeliverableStatus.IN_PROGRESS.value},
        )
        assert response.status_code == 200, response.text

        row = await _engagement_row(db)
        assert row.deliverables[0]["status"] == DeliverableStatus.IN_PROGRESS.value
        assert await _drain(db) == 1
        logs = await _audit_logs(db)
        assert [log.extra_metadata["event_type"] for log in logs] == [
            "DeliverableAdded",
            "DeliverableStatusChanged",
        ]
        assert _event(logs[-1])["from_status"] == DeliverableStatus.PENDING.value
        assert _event(logs[-1])["to_status"] == DeliverableStatus.IN_PROGRESS.value
        assert _event(logs[-1])["deliverable_id"] == deliverable_id
        assert logs[-1].user_id == USER_ID
        assert logs[-1].tenant_id == TENANT_ID

    async def test_logging_hours_reaches_audit_logs(self, api, db):
        response = await api.post(
            f"/engagements/{ENGAGEMENT_ID}/hours",
            json={"user_id": USER_ID, "logged_on": "2026-05-04", "hours": 3.5, "note": "Drafting"},
        )
        assert response.status_code == 201, response.text

        row = await _engagement_row(db)
        assert [entry["hours"] for entry in row.hours_log] == [3.5]
        assert await _drain(db) == 1
        logs = await _audit_logs(db)
        assert len(logs) == 1
        assert logs[0].extra_metadata["event_type"] == "HoursLogged"
        assert logs[0].tenant_id == TENANT_ID
        assert logs[0].user_id == USER_ID
        assert logs[0].resource_id == ENGAGEMENT_ID
        assert _event(logs[0])["hours"] == "3.5"


class TestAnAuditFailureRollsBackTheStateChange:
    async def test_a_failure_after_the_audit_call_leaves_no_deliverable_and_no_outbox_row(self, db):
        """The child mutation and its audit row commit together or not at all."""
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
            response = await client.post(
                f"/engagements/{ENGAGEMENT_ID}/deliverables",
                json={"title": "Will not survive", "description": None, "due_date": None},
            )

        assert failed["raised"] is True
        assert response.status_code == 500, response.text
        assert (await _engagement_row(db)).deliverables == []
        assert await _rows(db, OutboxEventModel) == []
        assert await _rows(db, AuditLogModel) == []
