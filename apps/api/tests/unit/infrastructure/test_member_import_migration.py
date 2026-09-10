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
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.schema import CreateSchema, DropSchema

from app.domain.value_objects.core import TenantId
from app.infrastructure.repositories.member_import_repository import MemberImportRepositoryImpl


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


async def test_find_batch_by_hash_picks_the_staged_one_when_others_share_it(migration_db):
    """A restage attempt must see the batch the unique index actually blocks on.

    An unfiltered query has no ORDER BY, so with an abandoned batch and a
    staged one sharing a hash, an arbitrary one can come back first. Picking
    the abandoned one would let a second stage attempt fall through the
    "already staged" check and hit the index at INSERT time as a raw
    IntegrityError instead of the intended 409.
    """
    connection, migration = migration_db
    await connection.run_sync(lambda conn: migrate(conn, migration.upgrade))
    await _insert_batch(connection, "b1", "sha256:same", "Abandoned")
    await _insert_batch(connection, "b2", "sha256:same", "Staged")

    session = AsyncSession(bind=connection, expire_on_commit=False)
    found = await MemberImportRepositoryImpl(session).find_batch_by_hash(
        TenantId("t1"), "sha256:same"
    )

    assert found is not None
    assert found.id.value == "b2"


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


async def _insert_row(connection, row_id: str, row_number: int, **values) -> None:
    columns = {
        "id": row_id,
        "tenant_id": "t1",
        "batch_id": "b1",
        "row_number": row_number,
        "outcome": "New",
        "decision": "import",
        "imported_member_id": None,
        **values,
    }
    names = ", ".join(columns)
    binds = ", ".join(f":{name}" for name in columns)
    await connection.execute(
        text(f"INSERT INTO member_import_rows ({names}) VALUES ({binds})"), columns
    )


async def test_restaging_a_file_reclaims_a_file_scoped_key_an_imported_row_holds(migration_db):
    """A dependant with no Staff_ID of their own is keyed by file and row number.

    That key is recomputed identically the next time the same file is staged,
    so a row still holding one after it imported collides with its own
    successor on (tenant_id, replay_key) and takes the whole insert down with
    it. Only the identity form, `key:{client}:{staff_id}`, is a claim worth
    keeping past a write.
    """
    connection, migration = migration_db
    await connection.run_sync(lambda conn: migrate(conn, migration.upgrade))
    await connection.execute(text("INSERT INTO eligible_members VALUES ('m1')"))
    await _insert_batch(connection, "b1", "sha256:same", "Applied")
    await _insert_row(
        connection,
        "r1",
        1,
        replay_key="file:sha256:same:row:2",
        imported_member_id="m1",
    )

    session = AsyncSession(bind=connection, expire_on_commit=False)
    released = await MemberImportRepositoryImpl(session).release_superseded_rows(
        TenantId("t1"), "sha256:same"
    )

    assert released == 1
    key = await connection.scalar(text("SELECT replay_key FROM member_import_rows WHERE id = 'r1'"))
    assert key == "released:b1:file:sha256:same:row:2"


async def test_an_imported_row_keeps_the_staff_id_it_claimed(migration_db):
    """The identity key is the whole point of a replay key; releasing it would
    let the next staging of the same file enrol that member a second time."""
    connection, migration = migration_db
    await connection.run_sync(lambda conn: migrate(conn, migration.upgrade))
    await connection.execute(text("INSERT INTO eligible_members VALUES ('m1')"))
    await _insert_batch(connection, "b1", "sha256:same", "Applied")
    await _insert_row(connection, "r1", 1, replay_key="key:c1:HR-1", imported_member_id="m1")

    session = AsyncSession(bind=connection, expire_on_commit=False)
    released = await MemberImportRepositoryImpl(session).release_superseded_rows(
        TenantId("t1"), "sha256:same"
    )

    assert released == 0
    key = await connection.scalar(text("SELECT replay_key FROM member_import_rows WHERE id = 'r1'"))
    assert key == "key:c1:HR-1"


async def test_downgrade_removes_both_tables(migration_db):
    connection, migration = migration_db
    await connection.run_sync(lambda conn: migrate(conn, migration.upgrade))
    await connection.run_sync(lambda conn: migrate(conn, migration.downgrade))
    tables = await connection.run_sync(lambda conn: inspect(conn).get_table_names())
    assert "member_import_batches" not in tables
    assert "member_import_rows" not in tables
