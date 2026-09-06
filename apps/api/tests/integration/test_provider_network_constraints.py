"""Composite foreign keys must reject cross-tenant writes in PostgreSQL.

Decision 3 requires database constraints, not only application checks, because
imports and maintenance scripts bypass the routes. An existence-only foreign
key would accept a provider from another tenant, so each case below writes a
mismatched tenant and asserts the database refuses it.
"""

import os
from uuid import uuid4

import pytest
import pytest_asyncio
from sqlalchemy import text
from sqlalchemy.engine import make_url
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy.schema import CreateSchema, DropSchema

from app.infrastructure.models.provider_affiliation_model import ProviderAffiliationModel
from app.infrastructure.models.provider_alias_model import ProviderAliasModel
from app.infrastructure.models.provider_organisation_model import ProviderOrganisationModel
from app.infrastructure.models.provider_specialty_model import (
    ProviderSpecialtyLinkModel,
    ProviderSpecialtyModel,
)
from app.infrastructure.models.session_import_model import (
    SessionImportBatchModel,
    SessionImportRowModel,
)

TENANT_A = "tenant-a"
TENANT_B = "tenant-b"

_PARENTS = """
CREATE TABLE tenants (id varchar(25) PRIMARY KEY);
CREATE TABLE service_sessions (id varchar(25) PRIMARY KEY);
CREATE TABLE providers (
    id varchar(25) PRIMARY KEY,
    tenant_id varchar(25) NOT NULL REFERENCES tenants (id),
    CONSTRAINT uq_providers_tenant_id UNIQUE (tenant_id, id)
);
"""

_TABLES = [
    ProviderOrganisationModel.__table__,
    ProviderAffiliationModel.__table__,
    ProviderSpecialtyModel.__table__,
    ProviderSpecialtyLinkModel.__table__,
    ProviderAliasModel.__table__,
    SessionImportBatchModel.__table__,
    SessionImportRowModel.__table__,
]


@pytest_asyncio.fixture
async def db():
    """Isolated schema in this worker's own database, dropped afterwards."""
    url = os.environ.get("MEMBER_TEST_DATABASE_URL")
    if not url:
        pytest.skip("Set MEMBER_TEST_DATABASE_URL to a local PostgreSQL database")
    assert make_url(url).host in {"localhost", "127.0.0.1", "::1"}
    schema = "provider_network_test_" + uuid4().hex
    engine = create_async_engine(url)
    try:
        async with engine.begin() as conn:
            await conn.execute(CreateSchema(schema))
            await conn.execute(text(f'SET LOCAL search_path TO "{schema}"'))
            for statement in filter(None, (s.strip() for s in _PARENTS.split(";"))):
                await conn.execute(text(statement))
            for table in _TABLES:
                await conn.run_sync(table.create)
            await conn.execute(
                text("INSERT INTO tenants (id) VALUES (:a), (:b)"), {"a": TENANT_A, "b": TENANT_B}
            )
            await conn.execute(
                text("INSERT INTO providers (id, tenant_id) VALUES ('prov-a', :a)"),
                {"a": TENANT_A},
            )
            await conn.execute(
                text("INSERT INTO providers (id, tenant_id) VALUES ('prov-b', :b)"),
                {"b": TENANT_B},
            )
            await conn.execute(
                text(
                    "INSERT INTO provider_organisations "
                    "(id, tenant_id, name, is_active, approval_status, created_at, updated_at) "
                    "VALUES ('org-a', :a, 'Firm A', true, 'Approved', now(), now())"
                ),
                {"a": TENANT_A},
            )
        engine_schema = create_async_engine(
            url, connect_args={"server_settings": {"search_path": schema}}
        )
        yield engine_schema
        await engine_schema.dispose()
    finally:
        async with engine.begin() as conn:
            await conn.execute(DropSchema(schema, cascade=True))
        await engine.dispose()


async def _insert(engine, sql: str, params: dict) -> None:
    async with engine.begin() as conn:
        await conn.execute(text(sql), params)


_AFFILIATION = (
    "INSERT INTO provider_affiliations "
    "(id, tenant_id, provider_id, organisation_id, valid_from, created_at, updated_at) "
    "VALUES (:id, :tenant, :provider, :org, DATE '2026-01-01', now(), now())"
)


class TestAffiliationTenantEnforcement:
    async def test_same_tenant_affiliation_is_accepted(self, db):
        await _insert(
            db,
            _AFFILIATION,
            {"id": "aff-1", "tenant": TENANT_A, "provider": "prov-a", "org": "org-a"},
        )

    async def test_provider_from_another_tenant_is_rejected(self, db):
        """prov-b exists, so an existence-only FK would have accepted this."""
        with pytest.raises(IntegrityError):
            await _insert(
                db,
                _AFFILIATION,
                {"id": "aff-2", "tenant": TENANT_A, "provider": "prov-b", "org": "org-a"},
            )

    async def test_organisation_from_another_tenant_is_rejected(self, db):
        with pytest.raises(IntegrityError):
            await _insert(
                db,
                _AFFILIATION,
                {"id": "aff-3", "tenant": TENANT_B, "provider": "prov-b", "org": "org-a"},
            )

    async def test_unknown_provider_is_rejected(self, db):
        with pytest.raises(IntegrityError):
            await _insert(
                db,
                _AFFILIATION,
                {"id": "aff-4", "tenant": TENANT_A, "provider": "nope", "org": "org-a"},
            )


class TestSpecialtyLinkTenantEnforcement:
    async def test_cross_tenant_provider_link_is_rejected(self, db):
        await _insert(
            db,
            "INSERT INTO provider_specialties (id, code, label, is_active, created_at, updated_at)"
            " VALUES ('spec-1', 'cbt', 'CBT', true, now(), now())",
            {},
        )
        with pytest.raises(IntegrityError):
            await _insert(
                db,
                "INSERT INTO provider_specialty_links "
                "(id, tenant_id, provider_id, specialty_id, created_at, updated_at) "
                "VALUES ('lnk-1', :tenant, 'prov-b', 'spec-1', now(), now())",
                {"tenant": TENANT_A},
            )

    async def test_a_global_specialty_carries_no_tenant_column(self, db):
        assert "tenant_id" not in ProviderSpecialtyModel.__table__.columns


class TestAliasScoping:
    _ALIAS = (
        "INSERT INTO provider_aliases "
        "(id, tenant_id, source_system, source_value, normalized_value, state, "
        " created_at, updated_at) "
        "VALUES (:id, :tenant, :source, 'Alice Nakato', 'alice nakato', 'Unmapped', "
        " now(), now())"
    )

    async def test_the_same_name_is_allowed_in_two_tenants(self, db):
        """Decision 5 forbids merging equal names across tenants."""
        await _insert(db, self._ALIAS, {"id": "al-1", "tenant": TENANT_A, "source": "sessions-csv"})
        await _insert(db, self._ALIAS, {"id": "al-2", "tenant": TENANT_B, "source": "sessions-csv"})

    async def test_the_same_name_is_allowed_in_two_source_systems(self, db):
        await _insert(db, self._ALIAS, {"id": "al-3", "tenant": TENANT_A, "source": "sessions-csv"})
        await _insert(db, self._ALIAS, {"id": "al-4", "tenant": TENANT_A, "source": "legacy-hr"})

    async def test_a_duplicate_within_one_tenant_and_source_is_rejected(self, db):
        await _insert(db, self._ALIAS, {"id": "al-5", "tenant": TENANT_A, "source": "sessions-csv"})
        with pytest.raises(IntegrityError):
            await _insert(
                db, self._ALIAS, {"id": "al-6", "tenant": TENANT_A, "source": "sessions-csv"}
            )

    async def test_a_resolved_alias_cannot_name_another_tenants_provider(self, db):
        with pytest.raises(IntegrityError):
            await _insert(
                db,
                "INSERT INTO provider_aliases "
                "(id, tenant_id, source_system, source_value, normalized_value, state, "
                " provider_id, created_at, updated_at) "
                "VALUES ('al-7', :tenant, 'sessions-csv', 'X', 'x', 'Resolved', 'prov-b', "
                " now(), now())",
                {"tenant": TENANT_A},
            )


class TestImportRowEnforcement:
    async def _batch(self, db):
        await _insert(
            db,
            "INSERT INTO session_import_batches "
            "(id, tenant_id, source_system, file_name, file_hash, row_count, status, "
            " staged_by, created_at, updated_at) "
            "VALUES ('b-1', :tenant, 'sessions-csv', 'f.csv', 'h1', 1, 'Staged', 'u-1', "
            " now(), now())",
            {"tenant": TENANT_A},
        )

    _ROW = (
        "INSERT INTO session_import_rows "
        "(id, tenant_id, batch_id, row_number, replay_key, outcome, delivery_context, "
        " provider_id, created_at, updated_at) "
        "VALUES (:id, :tenant, 'b-1', :n, :key, 'Accepted', 'Unknown', :provider, "
        " now(), now())"
    )

    async def test_a_same_tenant_row_is_accepted(self, db):
        await self._batch(db)
        await _insert(
            db,
            self._ROW,
            {"id": "r-1", "tenant": TENANT_A, "n": 1, "key": "k1", "provider": "prov-a"},
        )

    async def test_a_row_naming_another_tenants_provider_is_rejected(self, db):
        await self._batch(db)
        with pytest.raises(IntegrityError):
            await _insert(
                db,
                self._ROW,
                {"id": "r-2", "tenant": TENANT_A, "n": 2, "key": "k2", "provider": "prov-b"},
            )

    async def test_replaying_the_same_key_is_rejected(self, db):
        """Idempotency: one staged row per source record per tenant."""
        await self._batch(db)
        await _insert(
            db,
            self._ROW,
            {"id": "r-3", "tenant": TENANT_A, "n": 3, "key": "same", "provider": "prov-a"},
        )
        with pytest.raises(IntegrityError):
            await _insert(
                db,
                self._ROW,
                {"id": "r-4", "tenant": TENANT_A, "n": 4, "key": "same", "provider": "prov-a"},
            )

    async def test_a_duplicate_row_number_in_one_batch_is_rejected(self, db):
        await self._batch(db)
        await _insert(
            db,
            self._ROW,
            {"id": "r-5", "tenant": TENANT_A, "n": 5, "key": "k5", "provider": "prov-a"},
        )
        with pytest.raises(IntegrityError):
            await _insert(
                db,
                self._ROW,
                {"id": "r-6", "tenant": TENANT_A, "n": 5, "key": "k6", "provider": "prov-a"},
            )

    async def test_restaging_the_same_file_hash_in_one_tenant_is_rejected(self, db):
        await self._batch(db)
        with pytest.raises(IntegrityError):
            await _insert(
                db,
                "INSERT INTO session_import_batches "
                "(id, tenant_id, source_system, file_name, file_hash, row_count, status, "
                " staged_by, created_at, updated_at) "
                "VALUES ('b-2', :tenant, 'sessions-csv', 'again.csv', 'h1', 1, 'Staged', "
                " 'u-1', now(), now())",
                {"tenant": TENANT_A},
            )
