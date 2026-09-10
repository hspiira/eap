"""The writes that used to leave no trail, end to end.

Companion to test_audit_chain.py, which covers the aggregates that were
already audited. Every case here failed before: a platform vocabulary edit
could not be written at all, and the auth and DSAR routes never called the
audit path. Run with AUDIT_CHAIN_TEST_DATABASE_URL pointing at local
PostgreSQL.
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

from app.api.routes.auth import router as auth_router
from app.api.routes.client_tiers import router as client_tiers_router
from app.application.services.outbox_consumers import make_audit_consumer
from app.application.services.outbox_dispatcher import OutboxDispatcher
from app.core.authorization import require_platform_admin
from app.core.database import get_db
from app.core.exception_handlers import register_exception_handlers
from app.core.security import TokenData, get_current_user, hash_password
from app.domain.enums import (
    AuditActionType,
    SubscriptionTier,
    TenantRole,
    TenantStatus,
    UserStatus,
)
from app.infrastructure.models.audit_model import AuditLogModel, EntityChangeModel
from app.infrastructure.models.base import Base
from app.infrastructure.models.outbox_model import OutboxEventModel
from app.infrastructure.models.tenant_model import TenantModel
from app.infrastructure.models.user_model import UserModel
from app.infrastructure.repositories.audit_repository import AuditRepositoryImpl
from app.infrastructure.repositories.outbox_repository import OutboxRepositoryImpl
from app.shared.utils.datetime import utc_now
from app.shared.utils.route_audit_helper import PLATFORM_TENANT

TENANT_ID = "tenant-gaps-test"
TENANT_CODE = "gapst"
USER_ID = "user-gaps-test"
USER_EMAIL = "ops@gaps.test"
PASSWORD = "correct-horse-battery-staple"


@pytest_asyncio.fixture
async def chain_db():
    raw_url = os.environ.get("AUDIT_CHAIN_TEST_DATABASE_URL")
    if not raw_url:
        pytest.skip("Set AUDIT_CHAIN_TEST_DATABASE_URL to local PostgreSQL")
    url = make_url(raw_url)
    if url.host not in {"localhost", "127.0.0.1", "::1"}:
        pytest.fail("Audit chain tests require local PostgreSQL")
    schema = "audit_gaps_" + uuid4().hex
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
                name="Gaps test tenant",
                code=TENANT_CODE,
                settings={},
                status=TenantStatus.ACTIVE,
                subscription_tier=SubscriptionTier.FREE,
            )
        )
        await session.commit()

    async with sessions() as session:
        session.add(
            UserModel(
                id=USER_ID,
                tenant_id=TENANT_ID,
                email=USER_EMAIL,
                password_hash=hash_password(PASSWORD),
                role=TenantRole.ADMIN,
                status=UserStatus.ACTIVE,
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
    app = FastAPI()
    register_exception_handlers(app)
    app.include_router(auth_router)
    app.include_router(client_tiers_router)

    async def override_db():
        async with chain_db() as session:
            yield session

    async def override_user():
        return TokenData(user_id=USER_ID, tenant_id=TENANT_ID, email=USER_EMAIL)

    app.dependency_overrides[get_db] = override_db
    app.dependency_overrides[get_current_user] = override_user
    app.dependency_overrides[require_platform_admin] = override_user

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        yield client


async def _drain(sessions) -> int:
    async with sessions() as session:
        dispatcher = OutboxDispatcher(OutboxRepositoryImpl(session))
        dispatcher.register_consumer(make_audit_consumer(AuditRepositoryImpl(session)))
        delivered = await dispatcher.drain_once()
        await session.commit()
        return delivered


async def _logs(sessions) -> list[AuditLogModel]:
    async with sessions() as session:
        return list((await session.execute(select(AuditLogModel))).scalars().all())


class TestReferenceVocabulary:
    """A shared vocabulary belongs to no tenant, which is why it could not be logged."""

    async def test_creating_a_tier_reaches_audit_logs_under_the_platform_tenant(
        self, api, chain_db
    ):
        response = await api.post(
            "/client-tiers",
            json={"code": "gold", "name": "Gold", "description": None, "sort_order": 1},
            headers={"user-agent": "gaps-test", "x-forwarded-for": "203.0.113.9"},
        )
        assert response.status_code == 201, response.text

        assert await _drain(chain_db) == 1

        logs = await _logs(chain_db)
        assert len(logs) == 1
        assert logs[0].resource_type == "ClientTier"
        assert logs[0].action_type == AuditActionType.CREATE
        assert logs[0].user_id == USER_ID
        assert logs[0].ip_address == "203.0.113.9"
        # The row that the old foreign key made impossible: audit_logs.tenant_id
        # referenced tenants.id, and no tenant owns a shared vocabulary.
        assert logs[0].tenant_id == PLATFORM_TENANT

    async def test_renaming_a_tier_records_the_old_and_new_value(self, api, chain_db):
        created = await api.post(
            "/client-tiers",
            json={"code": "silver", "name": "Silver", "description": None, "sort_order": 2},
        )
        tier_id = created.json()["id"]
        response = await api.patch(f"/client-tiers/{tier_id}", json={"name": "Silver Plus"})
        assert response.status_code == 200, response.text

        assert await _drain(chain_db) == 2

        async with chain_db() as session:
            changes = (await session.execute(select(EntityChangeModel))).scalars().all()
        edited = {
            field["field_name"]: (field["old_value"], field["new_value"])
            for change in changes
            for field in change.field_changes
        }
        assert edited["name"] == ("Silver", "Silver Plus")


class TestAuthentication:
    async def test_a_granted_sign_in_is_recorded(self, api, chain_db):
        response = await api.post(
            "/auth/login",
            json={"tenant_code": TENANT_CODE, "email": USER_EMAIL, "password": PASSWORD},
            headers={"user-agent": "gaps-test", "x-forwarded-for": "203.0.113.9"},
        )
        assert response.status_code == 200, response.text

        assert await _drain(chain_db) == 1

        logs = await _logs(chain_db)
        assert len(logs) == 1
        assert logs[0].action_type == AuditActionType.LOGIN
        assert logs[0].resource_type == "Auth"
        assert logs[0].tenant_id == TENANT_ID
        assert logs[0].user_id == USER_ID
        assert logs[0].ip_address == "203.0.113.9"
        assert logs[0].extra_metadata["event_data"]["outcome"] == "granted"

    async def test_a_refused_sign_in_survives_the_rollback(self, api, chain_db):
        """A failed login raises, and @transactional rolls back what raised."""
        response = await api.post(
            "/auth/login",
            json={"tenant_code": TENANT_CODE, "email": USER_EMAIL, "password": "wrong"},
        )
        assert response.status_code == 401

        async with chain_db() as session:
            queued = (await session.execute(select(OutboxEventModel))).scalars().all()
        assert len(queued) == 1

        assert await _drain(chain_db) == 1

        logs = await _logs(chain_db)
        assert len(logs) == 1
        assert logs[0].action_type == AuditActionType.LOGIN
        assert logs[0].user_id == USER_ID
        assert logs[0].extra_metadata["event_data"]["outcome"] == "bad_password"

    async def test_an_unknown_tenant_writes_nothing(self, api, chain_db):
        """Deliberate: it changes no data, and an unauthenticated caller
        must not be able to fill the audit store."""
        response = await api.post(
            "/auth/login",
            json={"tenant_code": "nosuch", "email": USER_EMAIL, "password": PASSWORD},
        )
        assert response.status_code == 401

        async with chain_db() as session:
            queued = (await session.execute(select(OutboxEventModel))).scalars().all()
        assert queued == []
