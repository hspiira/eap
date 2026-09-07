"""Run the practitioner apply-ids migration against PostgreSQL, both directions."""

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

_PRECONDITIONS = (
    "CREATE TABLE practitioner_import_rows ("
    "id varchar(25) PRIMARY KEY, tenant_id varchar(25) NOT NULL)"
)

_COLUMNS = {"imported_provider_id", "imported_organisation_id", "imported_affiliation_id"}


def _migration():
    path = (
        Path(__file__).parents[3] / "alembic/versions/g1z4b6d8f0h2_practitioner_import_apply_ids.py"
    )
    spec = importlib.util.spec_from_file_location("practitioner_apply_migration", path)
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
    schema = "practitioner_apply_migration_" + uuid4().hex
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


async def _column_names(engine, schema: str) -> set[str]:
    async with engine.connect() as conn:
        return await conn.run_sync(
            lambda sync: {
                column["name"]
                for column in inspect(sync).get_columns("practitioner_import_rows", schema=schema)
            }
        )


class TestMigration:
    async def test_it_chains_from_the_session_row_resolution_revision(self):
        migration = _migration()
        assert migration.revision == "g1z4b6d8f0h2"
        assert migration.down_revision == "f0y3a5c7e9g1"

    async def test_upgrade_adds_the_three_nullable_id_columns(self, schema_engine):
        engine, schema = schema_engine
        async with engine.begin() as conn:
            await _run(conn, schema, "upgrade")
        assert _COLUMNS <= await _column_names(engine, schema)

    async def test_downgrade_removes_the_columns(self, schema_engine):
        engine, schema = schema_engine
        async with engine.begin() as conn:
            await _run(conn, schema, "upgrade")
        async with engine.begin() as conn:
            await _run(conn, schema, "downgrade")
        assert not _COLUMNS & await _column_names(engine, schema)
