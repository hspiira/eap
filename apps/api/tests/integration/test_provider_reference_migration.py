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
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy.schema import CreateSchema, DropSchema


@pytest_asyncio.fixture
async def migration_db():
    url = os.environ.get("MEMBER_TEST_DATABASE_URL")
    if not url:
        pytest.skip("Set MEMBER_TEST_DATABASE_URL to local PostgreSQL")
    assert make_url(url).host in {"localhost", "127.0.0.1", "::1"}
    schema = "provider_reference_migration_test_" + uuid4().hex
    engine = create_async_engine(url)
    spec = importlib.util.spec_from_file_location(
        "provider_reference_migration",
        Path(__file__).parents[2]
        / "alembic/versions/f6a8c0e2b4d6_constrain_provider_references.py",
    )
    migration = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(migration)
    try:
        async with engine.begin() as connection:
            await connection.execute(CreateSchema(schema))
            await connection.execute(text(f'SET LOCAL search_path TO "{schema}"'))
            await connection.execute(
                text(
                    "CREATE TABLE providers (id varchar(25) PRIMARY KEY, tenant_id varchar(25) NOT NULL)"
                )
            )
            await connection.execute(
                text(
                    "CREATE TABLE non_compete_clauses "
                    "(id varchar(25) PRIMARY KEY, tenant_id varchar(25) NOT NULL, provider_id varchar(25) NOT NULL)"
                )
            )
            await connection.execute(
                text(
                    "CREATE TABLE outreach_records "
                    "(id varchar(25) PRIMARY KEY, tenant_id varchar(25) NOT NULL, counsellor_id varchar(25))"
                )
            )
            await connection.execute(
                text("INSERT INTO providers VALUES ('provider-1', 'tenant-1')")
            )
        async with engine.begin() as connection:
            await connection.execute(text(f'SET LOCAL search_path TO "{schema}"'))
            yield connection, migration
    finally:
        async with engine.begin() as connection:
            await connection.execute(DropSchema(schema, cascade=True))
        await engine.dispose()


def migrate(connection, operation):
    with Operations.context(MigrationContext.configure(connection)):
        operation()


async def test_provider_reference_migration_enforces_constraints(migration_db):
    connection, migration = migration_db
    await connection.run_sync(lambda conn: migrate(conn, migration.upgrade))
    keys = await connection.run_sync(
        lambda conn: {
            tuple(key["constrained_columns"]): key["referred_table"]
            for table in ("non_compete_clauses", "outreach_records")
            for key in inspect(conn).get_foreign_keys(table)
        }
    )
    assert keys == {("provider_id",): "providers", ("counsellor_id",): "providers"}
    with pytest.raises(IntegrityError):
        await connection.execute(
            text("INSERT INTO non_compete_clauses VALUES ('clause-1', 'tenant-1', 'unknown')")
        )


async def test_provider_reference_migration_refuses_invalid_existing_data(migration_db):
    connection, migration = migration_db
    await connection.execute(
        text("INSERT INTO outreach_records VALUES ('outreach-1', 'tenant-1', 'unknown')")
    )
    with pytest.raises(RuntimeError, match="1 non-compete and 1 outreach"):
        await connection.run_sync(lambda conn: migrate(conn, migration.upgrade))
