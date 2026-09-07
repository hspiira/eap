"""The engagement-document checklist migration, forward and back on PostgreSQL.

Runs the real Alembic chain into a scratch schema, exercises the constraints
the table exists to enforce, then downgrades one step and upgrades again.

Run with MEMBER_TEST_DATABASE_URL pointing at local PostgreSQL.
"""

from pathlib import Path
from uuid import uuid4

import pytest
import pytest_asyncio
from alembic.config import Config
from sqlalchemy import text
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy.pool import NullPool

from alembic import command
from tests.integration._database_url import require_local_database

TENANT_A = "tenant-a"
TENANT_B = "tenant-b"
PARENT = "c7v0x2z4b6d8"

_PROFILE = (
    '{"tier": "T1", "region": "Central", "accreditation_status": "Accredited",'
    ' "panel_status": "Active"}'
)

_INSERT = (
    "INSERT INTO provider_engagement_documents"
    " (id, tenant_id, provider_id, document_kind, state, note, created_at, updated_at)"
    " VALUES (:id, :tenant, :provider, :kind, :state, :note, now(), now())"
)


def _config(url: str, schema: str) -> Config:
    root = Path(__file__).parents[2]
    config = Config(str(root / "alembic.ini"))
    config.set_main_option("script_location", str(root / "alembic"))
    config.set_main_option("sqlalchemy.url", url)
    config.set_main_option("version_table_schema", schema)
    return config


async def _alembic(engine, url: str, schema: str, action, target: str) -> None:
    config = _config(url, schema)

    def run(connection):
        config.attributes["connection"] = connection
        action(config, target)

    async with engine.begin() as connection:
        await connection.run_sync(run)


@pytest_asyncio.fixture
async def migrated():
    url = require_local_database("MEMBER_TEST_DATABASE_URL")
    schema = "engagement_docs_" + uuid4().hex
    admin = create_async_engine(url, poolclass=NullPool)
    async with admin.begin() as connection:
        await connection.execute(text(f'CREATE SCHEMA "{schema}"'))
    engine = create_async_engine(
        url, poolclass=NullPool, connect_args={"server_settings": {"search_path": schema}}
    )
    try:
        await _alembic(engine, url, schema, command.upgrade, "head")
        yield engine, schema, url
    finally:
        await engine.dispose()
        async with admin.begin() as connection:
            await connection.execute(text(f'DROP SCHEMA "{schema}" CASCADE'))
        await admin.dispose()


async def _seed(connection) -> None:
    for tenant in (TENANT_A, TENANT_B):
        await connection.execute(
            text(
                "INSERT INTO tenants (id, name, code, settings, status, subscription_tier,"
                " created_at, updated_at)"
                " VALUES (:id, :id, :code, '{}', 'Active', 'Free', now(), now())"
            ),
            {"id": tenant, "code": tenant[-6:]},
        )
    await connection.execute(
        text(
            "INSERT INTO providers (id, tenant_id, user_id, display_name,"
            " identity_provenance, status, provider_profile, created_at, updated_at)"
            f" VALUES ('prov-a', :tenant, NULL, 'Practitioner', 'Owned', 'Active', '{_PROFILE}',"
            " now(), now())"
        ),
        {"tenant": TENANT_A},
    )


async def _table_exists(engine, schema: str) -> bool:
    async with engine.begin() as connection:
        result = await connection.execute(
            text(
                "SELECT count(*) FROM information_schema.tables"
                " WHERE table_schema = :schema AND table_name = 'provider_engagement_documents'"
            ),
            {"schema": schema},
        )
        return result.scalar_one() == 1


class TestUpgrade:
    async def test_a_checklist_row_can_be_written(self, migrated):
        engine, _, _ = migrated
        async with engine.begin() as connection:
            await _seed(connection)
            await connection.execute(
                text(_INSERT),
                {
                    "id": "d1",
                    "tenant": TENANT_A,
                    "provider": "prov-a",
                    "kind": "Contract",
                    "state": "Present",
                    "note": "1year",
                },
            )

    async def test_a_second_row_for_the_same_kind_is_rejected(self, migrated):
        engine, _, _ = migrated
        async with engine.begin() as connection:
            await _seed(connection)
            await connection.execute(
                text(_INSERT),
                {
                    "id": "d1",
                    "tenant": TENANT_A,
                    "provider": "prov-a",
                    "kind": "KYC",
                    "state": "Missing",
                    "note": None,
                },
            )
        with pytest.raises(IntegrityError) as caught:
            async with engine.begin() as connection:
                await connection.execute(
                    text(_INSERT),
                    {
                        "id": "d2",
                        "tenant": TENANT_A,
                        "provider": "prov-a",
                        "kind": "KYC",
                        "state": "Open",
                        "note": None,
                    },
                )
        assert "uq_provider_engagement_documents_kind" in str(caught.value)

    async def test_a_cross_tenant_row_is_rejected_by_the_composite_key(self, migrated):
        engine, _, _ = migrated
        async with engine.begin() as connection:
            await _seed(connection)
        with pytest.raises(IntegrityError) as caught:
            async with engine.begin() as connection:
                await connection.execute(
                    text(_INSERT),
                    {
                        "id": "d3",
                        "tenant": TENANT_B,
                        "provider": "prov-a",
                        "kind": "Contract",
                        "state": "Present",
                        "note": None,
                    },
                )
        assert "fk_provider_engagement_documents_provider_tenant" in str(caught.value)


class TestDowngrade:
    async def test_downgrade_removes_the_table_and_upgrade_restores_it(self, migrated):
        engine, schema, url = migrated
        assert await _table_exists(engine, schema)
        await _alembic(engine, url, schema, command.downgrade, PARENT)
        assert not await _table_exists(engine, schema)
        await _alembic(engine, url, schema, command.upgrade, "head")
        assert await _table_exists(engine, schema)
