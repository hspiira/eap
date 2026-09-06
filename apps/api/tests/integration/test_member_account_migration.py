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
    schema = "member_account_migration_test_" + uuid4().hex
    engine = create_async_engine(url)
    spec = importlib.util.spec_from_file_location(
        "member_account_migration",
        Path(__file__).parents[2] / "alembic/versions/c9e1a3b5d7f9_add_member_account_links.py",
    )
    migration = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(migration)
    try:
        async with engine.begin() as connection:
            await connection.execute(CreateSchema(schema))
            await connection.execute(text(f'SET LOCAL search_path TO "{schema}"'))
            await connection.execute(text("CREATE TABLE users (id varchar(25) PRIMARY KEY)"))
            await connection.execute(
                text("CREATE TABLE eligible_members (id varchar(25) PRIMARY KEY)")
            )
            await connection.execute(text("INSERT INTO eligible_members VALUES ('member-1')"))
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


async def test_account_link_upgrade_preserves_members_and_enforces_one_to_one(migration_db):
    connection, migration = migration_db
    await connection.run_sync(lambda conn: migrate(conn, migration.upgrade))
    await connection.execute(text("INSERT INTO users VALUES ('user-1')"))
    await connection.execute(text("UPDATE eligible_members SET user_id = 'user-1'"))
    assert (
        await connection.execute(text("SELECT user_id FROM eligible_members WHERE id = 'member-1'"))
    ).scalar_one() == "user-1"

    await connection.execute(text("INSERT INTO eligible_members (id) VALUES ('member-2')"))
    with pytest.raises(IntegrityError):
        await connection.execute(
            text("UPDATE eligible_members SET user_id = 'user-1' WHERE id = 'member-2'")
        )


async def test_account_link_migration_roundtrip(migration_db):
    connection, migration = migration_db
    await connection.run_sync(lambda conn: migrate(conn, migration.upgrade))
    keys = await connection.run_sync(
        lambda conn: inspect(conn).get_foreign_keys("eligible_members")
    )
    assert {tuple(key["constrained_columns"]): key["referred_table"] for key in keys} == {
        ("user_id",): "users"
    }
    await connection.run_sync(lambda conn: migrate(conn, migration.downgrade))
    columns = await connection.run_sync(lambda conn: inspect(conn).get_columns("eligible_members"))
    assert "user_id" not in {column["name"] for column in columns}
