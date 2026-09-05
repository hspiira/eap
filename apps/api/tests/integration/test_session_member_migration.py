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


@pytest_asyncio.fixture
async def migration_db():
    url = os.environ.get("MEMBER_TEST_DATABASE_URL")
    if not url:
        pytest.skip("Set MEMBER_TEST_DATABASE_URL to local PostgreSQL")
    assert make_url(url).host in {"localhost", "127.0.0.1", "::1"}
    schema = "session_migration_test_" + uuid4().hex
    engine = create_async_engine(url)
    spec = importlib.util.spec_from_file_location(
        "member_migration",
        Path(__file__).parents[2] / "alembic/versions/a7c9e1f3b5d7_service_session_members.py",
    )
    migration = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(migration)
    try:
        async with engine.begin() as connection:
            await connection.execute(CreateSchema(schema))
            await connection.execute(text(f'SET LOCAL search_path TO "{schema}"'))
            for ddl in [
                "CREATE TABLE persons (id varchar(25) PRIMARY KEY)",
                "CREATE TABLE eligible_members (id varchar(25) PRIMARY KEY)",
                "CREATE TABLE service_sessions (id varchar(25) PRIMARY KEY, person_id varchar(25) NOT NULL REFERENCES persons(id), provider_id varchar(25) NOT NULL REFERENCES persons(id))",
                "CREATE INDEX ix_service_sessions_person_id ON service_sessions(person_id)",
            ]:
                await connection.execute(text(ddl))
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


async def test_empty_cutover_and_roundtrip(migration_db):
    connection, migration = migration_db
    await connection.run_sync(lambda c: migrate(c, migration.upgrade))
    keys = await connection.run_sync(lambda c: inspect(c).get_foreign_keys("service_sessions"))
    assert {tuple(k["constrained_columns"]): k["referred_table"] for k in keys} == {
        ("member_id",): "eligible_members",
        ("provider_id",): "persons",
    }
    await connection.run_sync(lambda c: migrate(c, migration.downgrade))
    columns = await connection.run_sync(lambda c: inspect(c).get_columns("service_sessions"))
    assert "person_id" in {c["name"] for c in columns}


async def test_existing_sessions_are_preserved_and_cutover_refused(migration_db):
    connection, migration = migration_db
    await connection.execute(text("INSERT INTO persons VALUES ('person-1')"))
    await connection.execute(
        text("INSERT INTO service_sessions VALUES ('session-1', 'person-1', 'person-1')")
    )
    with pytest.raises(RuntimeError, match="empty service_sessions"):
        await connection.run_sync(lambda c: migrate(c, migration.upgrade))
    assert (
        await connection.execute(text("SELECT person_id FROM service_sessions"))
    ).scalar_one() == "person-1"
