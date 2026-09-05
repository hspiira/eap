"""End-to-end outbox delivery against local PostgreSQL.

Covers the gap that let the audit trail stay empty in deployment: the unit
tests exercise the dispatcher against a fake repository, so nothing asserted
that an enqueued event actually becomes an audit_logs row. Run with
OUTBOX_TEST_DATABASE_URL pointing at local PostgreSQL.
"""

import os
from uuid import uuid4

import pytest
import pytest_asyncio
from sqlalchemy import func, select
from sqlalchemy.engine import make_url
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine
from sqlalchemy.pool import NullPool
from sqlalchemy.schema import CreateSchema, DropSchema

from app.application.services.outbox_consumers import make_audit_consumer
from app.application.services.outbox_dispatcher import OutboxDispatcher
from app.domain.enums import AuditActionType, SubscriptionTier, TenantStatus
from app.infrastructure.models.audit_model import AuditLogModel, EntityChangeModel
from app.infrastructure.models.base import Base
from app.infrastructure.models.outbox_model import OutboxEventModel
from app.infrastructure.models.tenant_model import TenantModel
from app.infrastructure.repositories.audit_repository import AuditRepositoryImpl
from app.infrastructure.repositories.outbox_repository import OutboxRepositoryImpl
from app.shared.utils.datetime import utc_now

TENANT_ID = "tenant-outbox-test"


@pytest_asyncio.fixture
async def outbox_db():
    raw_url = os.environ.get("OUTBOX_TEST_DATABASE_URL")
    if not raw_url:
        pytest.skip("Set OUTBOX_TEST_DATABASE_URL to local PostgreSQL")
    url = make_url(raw_url)
    if url.host not in {"localhost", "127.0.0.1", "::1"}:
        pytest.fail("Outbox delivery tests require local PostgreSQL")
    schema = "outbox_test_" + uuid4().hex
    admin = create_async_engine(url, poolclass=NullPool)
    async with admin.begin() as connection:
        await connection.execute(CreateSchema(schema))
    engine = create_async_engine(
        url, poolclass=NullPool, connect_args={"server_settings": {"search_path": schema}}
    )
    async with engine.begin() as connection:
        await connection.run_sync(Base.metadata.create_all)
    session_factory = async_sessionmaker(engine, expire_on_commit=False)
    async with session_factory() as session:
        session.add(
            TenantModel(
                id=TENANT_ID,
                name="Outbox test tenant",
                code="OUTBOX",
                settings={},
                status=TenantStatus.ACTIVE,
                subscription_tier=SubscriptionTier.FREE,
            )
        )
        await session.commit()
    try:
        yield session_factory
    finally:
        await engine.dispose()
        async with admin.begin() as connection:
            await connection.execute(DropSchema(schema, cascade=True))
        await admin.dispose()


def _payload(**overrides):
    payload = {
        "action_type": "UPDATE",
        "resource_type": "Client",
        "resource_id": "client-1",
        "user_id": "user-1",
        "event_type": "ClientSuspended",
        "ip_address": "203.0.113.4",
        "user_agent": "pytest",
        "field_changes": [
            {"field_name": "status", "old_value": "ACTIVE", "new_value": "SUSPENDED"}
        ],
        "is_special_category": False,
    }
    payload.update(overrides)
    return payload


async def _drain(session_factory) -> int:
    async with session_factory() as session:
        dispatcher = OutboxDispatcher(OutboxRepositoryImpl(session))
        dispatcher.register_consumer(make_audit_consumer(AuditRepositoryImpl(session)))
        delivered = await dispatcher.drain_once()
        await session.commit()
        return delivered


class TestOutboxDelivery:
    async def test_enqueued_event_becomes_audit_log(self, outbox_db):
        async with outbox_db() as session:
            await OutboxRepositoryImpl(session).enqueue(
                tenant_id=TENANT_ID,
                event_type="ClientSuspended",
                payload=_payload(),
                occurred_at=utc_now(),
                aggregate_type="Client",
                aggregate_id="client-1",
            )
            await session.commit()

        assert await _drain(outbox_db) == 1

        async with outbox_db() as session:
            logs = (await session.execute(select(AuditLogModel))).scalars().all()
            assert len(logs) == 1
            log = logs[0]
            assert log.tenant_id == TENANT_ID
            assert log.action_type == AuditActionType.UPDATE
            assert log.resource_type == "Client"
            assert log.resource_id == "client-1"
            assert log.user_id == "user-1"
            assert log.ip_address == "203.0.113.4"

            changes = (await session.execute(select(EntityChangeModel))).scalars().all()
            assert len(changes) == 1
            assert changes[0].audit_log_id == log.id
            assert changes[0].entity_type == "Client"
            assert changes[0].entity_id == "client-1"
            assert changes[0].field_changes == [
                {"field_name": "status", "old_value": "ACTIVE", "new_value": "SUSPENDED"}
            ]

    async def test_delivered_event_is_not_redelivered(self, outbox_db):
        async with outbox_db() as session:
            await OutboxRepositoryImpl(session).enqueue(
                tenant_id=TENANT_ID,
                event_type="ClientSuspended",
                payload=_payload(),
                occurred_at=utc_now(),
                aggregate_type="Client",
                aggregate_id="client-1",
            )
            await session.commit()

        assert await _drain(outbox_db) == 1
        assert await _drain(outbox_db) == 0

        async with outbox_db() as session:
            total = await session.scalar(select(func.count(AuditLogModel.id)))
            assert total == 1
            row = (await session.execute(select(OutboxEventModel))).scalars().one()
            assert row.delivered_at is not None
            assert row.last_error is None

    async def test_failed_delivery_is_retried_with_backoff(self, outbox_db):
        async with outbox_db() as session:
            await OutboxRepositoryImpl(session).enqueue(
                tenant_id=TENANT_ID,
                event_type="ClientSuspended",
                payload=_payload(action_type="NOT_A_VALID_ACTION"),
                occurred_at=utc_now(),
                aggregate_type="Client",
                aggregate_id="client-1",
            )
            await session.commit()

        assert await _drain(outbox_db) == 0

        async with outbox_db() as session:
            row = (await session.execute(select(OutboxEventModel))).scalars().one()
            assert row.delivered_at is None
            assert row.delivery_attempts == 1
            assert row.last_error
            assert row.next_attempt_at is not None
            assert await session.scalar(select(func.count(AuditLogModel.id))) == 0
