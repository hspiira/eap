"""Run the practitioner import migration against PostgreSQL, both directions."""

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

_PRECONDITIONS = "CREATE TABLE tenants (id varchar(25) PRIMARY KEY)"

_TABLES = {"practitioner_import_batches", "practitioner_import_rows"}


def _migration():
    path = (
        Path(__file__).parents[3] / "alembic/versions/e9x2z4b6d8f0_practitioner_import_staging.py"
    )
    spec = importlib.util.spec_from_file_location("practitioner_import_migration", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@pytest_asyncio.fixture
async def schema_engine():
    url = os.environ.get("TEST_DATABASE_URL")
    if not url:
        pytest.skip("Set TEST_DATABASE_URL to a local PostgreSQL database")
    if make_url(url).get_backend_name() != "postgresql":
        pytest.skip("The migration test needs PostgreSQL")
    assert make_url(url).host in {"localhost", "127.0.0.1", "::1"}
    schema = "practitioner_import_migration_" + uuid4().hex
    engine = create_async_engine(url)
    try:
        async with engine.begin() as conn:
            await conn.execute(CreateSchema(schema))
            await conn.execute(text(f'SET LOCAL search_path TO "{schema}"'))
            await conn.execute(text(_PRECONDITIONS))
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


async def _table_names(engine, schema: str) -> set[str]:
    async with engine.connect() as conn:
        return await conn.run_sync(lambda sync: set(inspect(sync).get_table_names(schema=schema)))


class TestMigration:
    async def test_it_chains_from_the_engagement_documents_revision(self):
        migration = _migration()
        assert migration.revision == "e9x2z4b6d8f0"
        assert migration.down_revision == "d8w1y3a5c7e9"

    async def test_upgrade_creates_both_tables(self, schema_engine):
        engine, schema = schema_engine
        async with engine.begin() as conn:
            await _run(conn, schema, "upgrade")
        assert _TABLES <= await _table_names(engine, schema)

    async def test_the_replay_key_is_unique_per_tenant(self, schema_engine):
        engine, schema = schema_engine
        async with engine.begin() as conn:
            await _run(conn, schema, "upgrade")
        async with engine.connect() as conn:
            rows = await conn.execute(
                text(
                    "SELECT conname FROM pg_constraint WHERE conrelid = "
                    "(:table)::regclass AND contype = 'u'"
                ),
                {"table": f"{schema}.practitioner_import_rows"},
            )
            names = {name for (name,) in rows}
        assert "uq_practitioner_import_rows_tenant_replay" in names
        assert "uq_practitioner_import_rows_batch_sheet_row" in names

    async def test_downgrade_removes_both_tables(self, schema_engine):
        engine, schema = schema_engine
        async with engine.begin() as conn:
            await _run(conn, schema, "upgrade")
        async with engine.begin() as conn:
            await _run(conn, schema, "downgrade")
        assert not _TABLES & await _table_names(engine, schema)
