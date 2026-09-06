"""Run the provider network migration against PostgreSQL, both directions.

The chain from base is agent 1's to assemble at gate 6. This exercises this
revision's own DDL against the preconditions it declares: tenants, providers
with uq_providers_tenant_id (added by a1p1c0d2e4f6), and service_sessions.
"""

import importlib.util
import os
from pathlib import Path
from uuid import uuid4

import pytest
import pytest_asyncio
from alembic.operations import Operations
from alembic.runtime.migration import MigrationContext
from sqlalchemy import inspect, text
from sqlalchemy.engine import make_url
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy.schema import CreateSchema, DropSchema

_PRECONDITIONS = """
CREATE TABLE tenants (id varchar(25) PRIMARY KEY);
CREATE TABLE service_sessions (id varchar(25) PRIMARY KEY);
CREATE TABLE providers (
    id varchar(25) PRIMARY KEY,
    tenant_id varchar(25) NOT NULL REFERENCES tenants (id),
    CONSTRAINT uq_providers_tenant_id UNIQUE (tenant_id, id)
);
"""

_EXPECTED = {
    "provider_specialties",
    "provider_organisations",
    "provider_affiliations",
    "provider_specialty_links",
    "provider_aliases",
    "session_import_batches",
    "session_import_rows",
}


def _migration():
    path = (
        Path(__file__).parents[2]
        / "alembic/versions/a2n1o0r2k4s6_provider_network_tables.py"
    )
    spec = importlib.util.spec_from_file_location("provider_network_migration", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@pytest_asyncio.fixture
async def schema_engine():
    url = os.environ.get("MEMBER_TEST_DATABASE_URL")
    if not url:
        pytest.skip("Set MEMBER_TEST_DATABASE_URL to a local PostgreSQL database")
    assert make_url(url).host in {"localhost", "127.0.0.1", "::1"}
    schema = "provider_network_migration_" + uuid4().hex
    engine = create_async_engine(url)
    try:
        async with engine.begin() as conn:
            await conn.execute(CreateSchema(schema))
        yield engine, schema
    finally:
        async with engine.begin() as conn:
            await conn.execute(DropSchema(schema, cascade=True))
        await engine.dispose()


async def _run(conn, schema: str, direction: str) -> None:
    await conn.execute(text(f'SET LOCAL search_path TO "{schema}"'))
    migration = _migration()

    def _apply(sync_conn):
        context = MigrationContext.configure(sync_conn)
        with Operations.context(context):
            getattr(migration, direction)()

    await conn.run_sync(_apply)


class TestMigration:
    async def test_revision_chains_from_the_agreed_parent(self):
        """Agent 1 reserved a1p2i0d2e4f6 for me to chain from."""
        migration = _migration()
        assert migration.revision == "a2n1o0r2k4s6"
        assert migration.down_revision == "a1p2i0d2e4f6"

    async def test_upgrade_creates_every_table(self, schema_engine):
        engine, schema = schema_engine
        async with engine.begin() as conn:
            await conn.execute(text(f'SET LOCAL search_path TO "{schema}"'))
            for statement in filter(None, (s.strip() for s in _PRECONDITIONS.split(";"))):
                await conn.execute(text(statement))
        async with engine.begin() as conn:
            await _run(conn, schema, "upgrade")
        async with engine.connect() as conn:
            names = await conn.run_sync(
                lambda sync: set(inspect(sync).get_table_names(schema=schema))
            )
        assert _EXPECTED <= names

    async def test_the_composite_keys_survive_the_migration(self, schema_engine):
        """The DDL must produce the tenant-carrying keys, not plain ones."""
        engine, schema = schema_engine
        async with engine.begin() as conn:
            await conn.execute(text(f'SET LOCAL search_path TO "{schema}"'))
            for statement in filter(None, (s.strip() for s in _PRECONDITIONS.split(";"))):
                await conn.execute(text(statement))
        async with engine.begin() as conn:
            await _run(conn, schema, "upgrade")
        async with engine.connect() as conn:
            rows = await conn.execute(
                text(
                    "SELECT conname, pg_get_constraintdef(oid) FROM pg_constraint "
                    "WHERE conrelid = (:table)::regclass AND contype = 'f'"
                ),
                {"table": f"{schema}.provider_affiliations"},
            )
            definitions = {name: definition for name, definition in rows}
        provider_key = definitions["fk_provider_affiliations_tenant_provider"]
        assert "tenant_id, provider_id" in provider_key
        assert "tenant_id, id" in provider_key

    async def test_downgrade_removes_every_table(self, schema_engine):
        engine, schema = schema_engine
        async with engine.begin() as conn:
            await conn.execute(text(f'SET LOCAL search_path TO "{schema}"'))
            for statement in filter(None, (s.strip() for s in _PRECONDITIONS.split(";"))):
                await conn.execute(text(statement))
        async with engine.begin() as conn:
            await _run(conn, schema, "upgrade")
        async with engine.begin() as conn:
            await _run(conn, schema, "downgrade")
        async with engine.connect() as conn:
            names = await conn.run_sync(
                lambda sync: set(inspect(sync).get_table_names(schema=schema))
            )
        assert not (_EXPECTED & names)
        assert "providers" in names
