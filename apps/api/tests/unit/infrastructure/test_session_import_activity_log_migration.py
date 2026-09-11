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
    schema = "session_import_activity_log_test_" + uuid4().hex
    engine = create_async_engine(url)
    spec = importlib.util.spec_from_file_location(
        "session_import_row_activity_log_fields",
        Path(__file__).parents[3]
        / "alembic/versions/f2h4j6l8n0p2_session_import_row_activity_log_fields.py",
    )
    migration = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(migration)
    try:
        async with engine.begin() as connection:
            await connection.execute(CreateSchema(schema))
            await connection.execute(text(f'SET LOCAL search_path TO "{schema}"'))
            # A minimal stand-in for the real table, which earlier migrations create.
            await connection.execute(
                text(
                    "CREATE TABLE session_import_rows ("
                    "id varchar(25) PRIMARY KEY, tenant_id varchar(25), "
                    "batch_id varchar(25), row_number integer)"
                )
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


async def test_upgrade_adds_the_four_enrichment_columns(migration_db):
    connection, migration = migration_db
    await connection.run_sync(lambda conn: migrate(conn, migration.upgrade))

    columns = {
        column["name"]
        for column in await connection.run_sync(
            lambda conn: inspect(conn).get_columns("session_import_rows")
        )
    }
    assert {"issue_topic", "diagnosis_type_id", "diagnosis_id", "approved_by"} <= columns
    assert "feedback" not in columns


async def test_downgrade_removes_them_again(migration_db):
    connection, migration = migration_db
    await connection.run_sync(lambda conn: migrate(conn, migration.upgrade))
    await connection.run_sync(lambda conn: migrate(conn, migration.downgrade))

    columns = {
        column["name"]
        for column in await connection.run_sync(
            lambda conn: inspect(conn).get_columns("session_import_rows")
        )
    }
    assert not ({"issue_topic", "diagnosis_type_id", "diagnosis_id", "approved_by"} & columns)
