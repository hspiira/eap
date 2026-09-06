"""The audit trail, end to end, as it works in deployment.

An HTTP mutation writes an outbox row in its own transaction; the worker
process drains that row into audit_logs and entity_changes; the audit API
then returns it. Every previous test covered one segment of that chain, which
is how three separate faults survived in the middle of it. Run with
AUDIT_CHAIN_TEST_DATABASE_URL pointing at local PostgreSQL.
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

from app.api.routes.clients import router as clients_router
from app.application.services.outbox_consumers import make_audit_consumer
from app.application.services.outbox_dispatcher import OutboxDispatcher
from app.core.database import get_db
from app.core.exception_handlers import register_exception_handlers
from app.core.security import TokenData, get_current_user
from app.domain.enums import AuditActionType, BaseStatus, SubscriptionTier, TenantStatus
from app.infrastructure.models.audit_model import AuditLogModel, EntityChangeModel
from app.infrastructure.models.base import Base
from app.infrastructure.models.client_model import ClientModel
from app.infrastructure.models.outbox_model import OutboxEventModel
from app.infrastructure.models.tenant_model import TenantModel
from app.infrastructure.repositories.audit_repository import AuditRepositoryImpl
from app.infrastructure.repositories.outbox_repository import OutboxRepositoryImpl
from app.shared.utils.datetime import utc_now

TENANT_ID = "tenant-chain-test"
USER_ID = "user-chain-test"
CLIENT_ID = "client-chain-test"


@pytest_asyncio.fixture
async def chain_db():
    raw_url = os.environ.get("AUDIT_CHAIN_TEST_DATABASE_URL")
    if not raw_url:
        pytest.skip("Set AUDIT_CHAIN_TEST_DATABASE_URL to local PostgreSQL")
    url = make_url(raw_url)
    if url.host not in {"localhost", "127.0.0.1", "::1"}:
        pytest.fail("Audit chain tests require local PostgreSQL")
    schema = "audit_chain_" + uuid4().hex
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
                name="Chain test tenant",
                code="chaint",
                settings={},
                status=TenantStatus.ACTIVE,
                subscription_tier=SubscriptionTier.FREE,
            )
        )
        await session.commit()

    async with sessions() as session:
        session.add(
            ClientModel(
                id=CLIENT_ID,
                tenant_id=TENANT_ID,
                name="Acme Corp",
                code="ACME",
                status=BaseStatus.ACTIVE,
                contact_info={"phone": "+441234567890", "email": "ops@acme.test"},
                is_verified=True,
                created_at=utc_now(),
                updated_at=utc_now(),
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


@pytest_asyncio.fixture
async def api(chain_db):
    """The client routes wired to the test schema, with auth stubbed."""
    app = FastAPI()
    register_exception_handlers(app)
    app.include_router(clients_router)

    async def override_db():
        async with chain_db() as session:
            yield session

    async def override_user():
        return TokenData(user_id=USER_ID, tenant_id=TENANT_ID, email="ops@acme.test")

    app.dependency_overrides[get_db] = override_db
    app.dependency_overrides[get_current_user] = override_user

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        yield client


async def _drain(sessions) -> int:
    """Run the dispatcher the worker process runs."""
    async with sessions() as session:
        dispatcher = OutboxDispatcher(OutboxRepositoryImpl(session))
        dispatcher.register_consumer(make_audit_consumer(AuditRepositoryImpl(session)))
        delivered = await dispatcher.drain_once()
        await session.commit()
        return delivered


class TestAuditChain:
    async def test_a_suspension_travels_from_http_to_audit_logs(self, api, chain_db):
        response = await api.post(
            f"/clients/{CLIENT_ID}/suspend",
            json={"reason": "Non-payment"},
            headers={"user-agent": "chain-test", "x-forwarded-for": "203.0.113.9"},
        )
        assert response.status_code == 200, response.text
        # Suspension parks a client in INACTIVE; there is no separate status.
        assert response.json()["status"] == BaseStatus.INACTIVE.value

        # The request commits an outbox row and no audit row: the worker owns
        # that write, and it has not run yet.
        async with chain_db() as session:
            assert len((await session.execute(select(OutboxEventModel))).scalars().all()) == 1
            assert len((await session.execute(select(AuditLogModel))).scalars().all()) == 0

        assert await _drain(chain_db) == 1

        async with chain_db() as session:
            logs = (await session.execute(select(AuditLogModel))).scalars().all()
            assert len(logs) == 1
            log = logs[0]
            assert log.tenant_id == TENANT_ID
            assert log.user_id == USER_ID
            assert log.resource_type == "Client"
            assert log.resource_id == CLIENT_ID
            assert log.ip_address == "203.0.113.9"
            assert log.user_agent == "chain-test"
            assert log.occurred_at.tzinfo is not None
            assert log.action_type == AuditActionType.REJECT
            assert log.extra_metadata["event_type"] == "ClientSuspended"

            # No entity_changes row: field changes are only extracted for CREATE
            # and for UPDATE with an old_entity, and the suspend route passes
            # neither. The audit log records that it happened, not what changed.
            changes = (await session.execute(select(EntityChangeModel))).scalars().all()
            assert changes == []

    async def test_a_failed_request_writes_no_outbox_row(self, api, chain_db):
        response = await api.post("/clients/does-not-exist/suspend", json={"reason": "Non-payment"})
        assert response.status_code in {403, 404}

        async with chain_db() as session:
            assert len((await session.execute(select(OutboxEventModel))).scalars().all()) == 0

        assert await _drain(chain_db) == 0
