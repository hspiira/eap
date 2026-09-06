"""The provider migrations, run as Alembic runs them, against real PostgreSQL.

The previous version of this file built three stub tables by hand and asserted
on a rejection message. Its fixture inserted one invalid outreach row and no
clause but expected "1 non-compete and 1 outreach", so it pinned the message
rather than the DDL, and it exercised no part of the real chain.

These upgrade the actual chain into a scratch schema and then attempt the
writes the constraints exist to stop. A composite key that is not doing its
job fails here, where an existence-only foreign key would pass.

Run with MEMBER_TEST_DATABASE_URL pointing at local PostgreSQL.
"""

from pathlib import Path
from uuid import uuid4

import pytest
import pytest_asyncio
from alembic.config import Config
from sqlalchemy import inspect, text
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy.pool import NullPool

from alembic import command
from tests.integration._database_url import require_local_database

TENANT_A = "tenant-a"
TENANT_B = "tenant-b"

BOUNDARY_PARENT = "f6a8c0e2b4d6"

_PROFILE = (
    '{"tier": "T1", "region": "Central", "accreditation_status": "Accredited",'
    ' "panel_status": "Active"}'
)


def _url() -> str:
    return require_local_database("MEMBER_TEST_DATABASE_URL")


def _config(url: str, schema: str) -> Config:
    root = Path(__file__).parents[2]
    config = Config(str(root / "alembic.ini"))
    config.set_main_option("script_location", str(root / "alembic"))
    config.set_main_option("sqlalchemy.url", url)
    config.set_main_option("version_table_schema", schema)
    return config


async def _alembic(engine, url: str, schema: str, action, target: str) -> None:
    """Run one Alembic command over an async connection."""
    config = _config(url, schema)

    def run(connection):
        config.attributes["connection"] = connection
        action(config, target)

    async with engine.begin() as connection:
        await connection.run_sync(run)


@pytest_asyncio.fixture
async def migrated():
    """The real chain upgraded to head inside a scratch schema."""
    url = _url()
    schema = "provider_migration_" + uuid4().hex
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


async def _seed_tenants(connection) -> None:
    for tenant in (TENANT_A, TENANT_B):
        await connection.execute(
            text(
                "INSERT INTO tenants (id, name, code, settings, status, subscription_tier,"
                " created_at, updated_at)"
                " VALUES (:id, :id, :code, '{}', 'Active', 'Free', now(), now())"
            ),
            {"id": tenant, "code": tenant[-6:]},
        )


async def _seed_provider(connection, provider_id: str, tenant_id: str) -> None:
    await connection.execute(
        text(
            "INSERT INTO providers (id, tenant_id, user_id, display_name,"
            " identity_provenance, status, provider_profile, created_at, updated_at)"
            f" VALUES (:id, :tenant, NULL, 'Practitioner', 'Owned', 'Active', '{_PROFILE}',"
            " now(), now())"
        ),
        {"id": provider_id, "tenant": tenant_id},
    )


async def _rejects(engine, statement: str, params: dict, *, constraint: str) -> None:
    """The write must fail, and fail on the named constraint.

    Naming it matters: a NOT NULL violation in the fixture would otherwise
    satisfy a bare pytest.raises and report a constraint as working when it
    was never reached.
    """
    with pytest.raises(IntegrityError) as caught:
        async with engine.begin() as connection:
            await connection.execute(text(statement), params)
    assert constraint in str(caught.value), f"expected {constraint} to reject this write"


class TestCompositeTenantConstraints:
    async def test_the_chain_reaches_a_single_head(self, migrated):
        engine, _, _ = migrated
        async with engine.connect() as connection:
            revisions = (
                await connection.execute(text("SELECT version_num FROM alembic_version"))
            ).all()
        assert len(revisions) == 1, "the chain must not leave multiple heads"

    async def test_provider_references_are_composite_not_existence_only(self, migrated):
        """Each reference keys on (tenant_id, id), so tenant equality is enforced."""
        engine, _, _ = migrated

        def read(connection):
            return {
                (table, tuple(key["constrained_columns"])): tuple(key["referred_columns"])
                for table in ("non_compete_clauses", "outreach_records", "service_sessions")
                for key in inspect(connection).get_foreign_keys(table)
                if key["referred_table"] == "providers"
            }

        async with engine.connect() as connection:
            keys = await connection.run_sync(read)
        assert keys == {
            ("non_compete_clauses", ("tenant_id", "provider_id")): ("tenant_id", "id"),
            ("outreach_records", ("tenant_id", "counsellor_id")): ("tenant_id", "id"),
            ("service_sessions", ("tenant_id", "provider_id")): ("tenant_id", "id"),
        }

    async def test_a_cross_tenant_non_compete_clause_is_rejected(self, migrated):
        engine, _, _ = migrated
        async with engine.begin() as connection:
            await _seed_tenants(connection)
            await _seed_provider(connection, "provider-a", TENANT_A)
        await _rejects(
            engine,
            "INSERT INTO non_compete_clauses (id, tenant_id, provider_id, status,"
            " terms_summary, effective_from, created_at, updated_at)"
            " VALUES ('clause-x', :tenant, 'provider-a', 'Draft', 'terms',"
            " current_date, now(), now())",
            {"tenant": TENANT_B},
            constraint="fk_non_compete_clauses_provider_tenant",
        )

    async def test_a_cross_tenant_outreach_assignment_is_rejected(self, migrated):
        """The composite key stops what the earlier existence-only key allowed."""
        engine, _, _ = migrated
        async with engine.begin() as connection:
            await _seed_tenants(connection)
            await _seed_provider(connection, "provider-a", TENANT_A)
            await connection.execute(
                text(
                    "INSERT INTO care_callback_campaigns (id, tenant_id, client_id, name,"
                    " period_start, period_end, target_count, completed_count, counsellor_pool,"
                    " status, created_by, created_at, updated_at)"
                    " VALUES ('camp-1', :tenant, 'client-1', 'Campaign', current_date,"
                    " current_date, 0, 0, '[]', 'Draft', 'user-1', now(), now())"
                ),
                {"tenant": TENANT_B},
            )
            await connection.execute(
                text(
                    "INSERT INTO eligible_members (id, tenant_id, client_id,"
                    " employer_member_id, relation, status, created_at, updated_at)"
                    " VALUES ('member-1', :tenant, 'client-1', 'EMP-1', 'Employee',"
                    " 'Active', now(), now())"
                ),
                {"tenant": TENANT_B},
            )
        await _rejects(
            engine,
            "INSERT INTO outreach_records (id, tenant_id, campaign_id, member_id,"
            " counsellor_id, status, contact_attempts, crisis_flag, created_at, updated_at)"
            " VALUES ('outreach-x', :tenant, 'camp-1', 'member-1', 'provider-a',"
            " 'Pending', 0, false, now(), now())",
            {"tenant": TENANT_B},
            constraint="fk_outreach_records_counsellor_tenant",
        )

    async def test_an_unknown_provider_reference_is_still_rejected(self, migrated):
        engine, _, _ = migrated
        async with engine.begin() as connection:
            await _seed_tenants(connection)
        await _rejects(
            engine,
            "INSERT INTO non_compete_clauses (id, tenant_id, provider_id, status,"
            " terms_summary, effective_from, created_at, updated_at)"
            " VALUES ('clause-y', :tenant, 'nobody', 'Draft', 'terms',"
            " current_date, now(), now())",
            {"tenant": TENANT_A},
            constraint="fk_non_compete_clauses_provider_tenant",
        )


class TestOwnedIdentity:
    async def test_a_practitioner_can_exist_without_an_account(self, migrated):
        engine, _, _ = migrated
        async with engine.begin() as connection:
            await _seed_tenants(connection)
            await _seed_provider(connection, "provider-a", TENANT_A)
        async with engine.connect() as connection:
            row = (
                await connection.execute(
                    text("SELECT user_id, display_name FROM providers WHERE id = 'provider-a'")
                )
            ).one()
        assert row.user_id is None
        assert row.display_name == "Practitioner"

    async def test_one_account_links_to_at_most_one_practitioner_per_tenant(self, migrated):
        engine, _, _ = migrated
        async with engine.begin() as connection:
            await _seed_tenants(connection)
            await connection.execute(
                text(
                    "INSERT INTO users (id, tenant_id, email, status, role,"
                    " is_two_factor_enabled, created_at, updated_at)"
                    " VALUES ('user-1', :tenant, 'u@example.test', 'Active', 'User', false,"
                    " now(), now())"
                ),
                {"tenant": TENANT_A},
            )
            for provider_id in ("provider-a", "provider-b"):
                await _seed_provider(connection, provider_id, TENANT_A)
            await connection.execute(
                text("UPDATE providers SET user_id = 'user-1' WHERE id = 'provider-a'")
            )
        await _rejects(
            engine,
            "UPDATE providers SET user_id = 'user-1' WHERE id = 'provider-b'",
            {},
            constraint="uq_providers_tenant_user_link",
        )

    async def test_several_practitioners_may_have_no_account(self, migrated):
        """The uniqueness rule is partial, so NULL links do not collide."""
        engine, _, _ = migrated
        async with engine.begin() as connection:
            await _seed_tenants(connection)
            for provider_id in ("provider-a", "provider-b", "provider-c"):
                await _seed_provider(connection, provider_id, TENANT_A)
        async with engine.connect() as connection:
            count = (
                await connection.execute(
                    text("SELECT count(*) FROM providers WHERE user_id IS NULL")
                )
            ).scalar_one()
        assert count == 3


class TestUpgradeAndRollback:
    async def test_the_provider_migrations_downgrade_and_re_upgrade(self, migrated):
        """Rehearses the rollback both provider migrations would need."""
        engine, schema, url = migrated

        def columns(connection):
            return {c["name"] for c in inspect(connection).get_columns("providers")}

        await _alembic(engine, url, schema, command.downgrade, BOUNDARY_PARENT)
        async with engine.connect() as connection:
            assert "display_name" not in await connection.run_sync(columns)

        await _alembic(engine, url, schema, command.upgrade, "head")
        async with engine.connect() as connection:
            after = await connection.run_sync(columns)
        assert {"display_name", "contact_email", "identity_provenance"} <= after
