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
    schema = "member_import_migration_test_" + uuid4().hex
    engine = create_async_engine(url)
    spec = importlib.util.spec_from_file_location(
        "member_import_staging",
        Path(__file__).parents[3] / "alembic/versions/n3q5s7u9w1y3_member_import_staging.py",
    )
    migration = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(migration)
    try:
        async with engine.begin() as connection:
            await connection.execute(CreateSchema(schema))
            await connection.execute(text(f'SET LOCAL search_path TO "{schema}"'))
            await connection.execute(text("CREATE TABLE tenants (id varchar(25) PRIMARY KEY)"))
            await connection.execute(
                text("CREATE TABLE eligible_members (id varchar(25) PRIMARY KEY)")
            )
            await connection.execute(text("INSERT INTO tenants VALUES ('t1')"))
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


async def _insert_batch(connection, batch_id: str, file_hash: str, status: str) -> None:
    await connection.execute(
        text(
            "INSERT INTO member_import_batches "
            "(id, tenant_id, file_name, file_hash, status, staged_by) "
            "VALUES (:id, 't1', 'roster.csv', :file_hash, :status, 'u1')"
        ),
        {"id": batch_id, "file_hash": file_hash, "status": status},
    )


async def test_upgrade_creates_batches_and_rows_with_expected_shape(migration_db):
    connection, migration = migration_db
    await connection.run_sync(lambda conn: migrate(conn, migration.upgrade))

    batch_columns = {
        column["name"]
        for column in await connection.run_sync(
            lambda conn: inspect(conn).get_columns("member_import_batches")
        )
    }
    assert {"id", "tenant_id", "file_name", "file_hash", "status", "staged_by"} <= batch_columns

    row_columns = {
        column["name"]
        for column in await connection.run_sync(
            lambda conn: inspect(conn).get_columns("member_import_rows")
        )
    }
    assert {
        "batch_id",
        "replay_key",
        "import_source_id",
        "outcome",
        "decision",
        "imported_member_id",
    } <= row_columns

    fks = await connection.run_sync(
        lambda conn: inspect(conn).get_foreign_keys("member_import_rows")
    )
    referred = {fk["referred_table"] for fk in fks}
    assert referred == {"member_import_batches", "tenants", "eligible_members"}


async def test_only_a_staged_batch_holds_its_file_hash(migration_db):
    connection, migration = migration_db
    await connection.run_sync(lambda conn: migrate(conn, migration.upgrade))

    await _insert_batch(connection, "b1", "sha256:same", "Staged")
    with pytest.raises(IntegrityError):
        await _insert_batch(connection, "b2", "sha256:same", "Staged")


async def test_an_applied_batch_does_not_block_restaging_the_same_file(migration_db):
    connection, migration = migration_db
    await connection.run_sync(lambda conn: migrate(conn, migration.upgrade))

    await _insert_batch(connection, "b1", "sha256:same", "Applied")
    # Should not raise: only a still-Staged batch holds the hash.
    await _insert_batch(connection, "b2", "sha256:same", "Staged")


async def test_a_replay_key_is_unique_per_tenant(migration_db):
    connection, migration = migration_db
    await connection.run_sync(lambda conn: migrate(conn, migration.upgrade))
    await _insert_batch(connection, "b1", "sha256:one", "Staged")
    await connection.execute(
        text(
            "INSERT INTO member_import_rows "
            "(id, tenant_id, batch_id, row_number, replay_key, outcome, decision) "
            "VALUES ('r1', 't1', 'b1', 1, 'key:c1:HR-1', 'New', 'import')"
        )
    )
    with pytest.raises(IntegrityError):
        await connection.execute(
            text(
                "INSERT INTO member_import_rows "
                "(id, tenant_id, batch_id, row_number, replay_key, outcome, decision) "
                "VALUES ('r2', 't1', 'b1', 2, 'key:c1:HR-1', 'New', 'import')"
            )
        )


async def test_downgrade_removes_both_tables(migration_db):
    connection, migration = migration_db
    await connection.run_sync(lambda conn: migrate(conn, migration.upgrade))
    await connection.run_sync(lambda conn: migrate(conn, migration.downgrade))
    tables = await connection.run_sync(lambda conn: inspect(conn).get_table_names())
    assert "member_import_batches" not in tables
    assert "member_import_rows" not in tables
