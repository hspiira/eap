"""get_valid_affiliation against PostgreSQL, including agent 1's acceptance cases.

The eligibility path treats a None result as "cannot deliver through this
affiliation", so every rejection below must be None rather than an exception.
The boundary day is resolved in Africa/Kampala, agreed with agent 1 and matching
decision 7's adopted default for accreditation expiry.
"""

import os
from datetime import UTC, date, datetime
from uuid import uuid4
from zoneinfo import ZoneInfo

import pytest
import pytest_asyncio
from sqlalchemy import text
from sqlalchemy.engine import make_url
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine
from sqlalchemy.schema import CreateSchema, DropSchema

from app.domain.value_objects.core import ProviderId, TenantId
from app.domain.value_objects.provider_network import (
    ProviderAffiliationId,
    ProviderOrganisationId,
)
from app.infrastructure.models.provider_affiliation_model import ProviderAffiliationModel
from app.infrastructure.models.provider_organisation_model import ProviderOrganisationModel
from app.infrastructure.repositories.provider_network_repository import (
    ProviderAffiliationRepositoryImpl,
    ProviderOrganisationRepositoryImpl,
)

KAMPALA = ZoneInfo("Africa/Kampala")
TENANT_A = TenantId("tenant-a")
TENANT_B = TenantId("tenant-b")
PROV_A = ProviderId("prov-a")
PROV_B = ProviderId("prov-b")
AFF = ProviderAffiliationId("aff-1")
ORG = ProviderOrganisationId("org-a")

_PARENTS = """
CREATE TABLE tenants (id varchar(25) PRIMARY KEY);
CREATE TABLE providers (
    id varchar(25) PRIMARY KEY,
    tenant_id varchar(25) NOT NULL REFERENCES tenants (id),
    CONSTRAINT uq_providers_tenant_id UNIQUE (tenant_id, id)
);
"""


@pytest_asyncio.fixture
async def session_factory():
    url = os.environ.get("MEMBER_TEST_DATABASE_URL")
    if not url:
        pytest.skip("Set MEMBER_TEST_DATABASE_URL to a local PostgreSQL database")
    assert make_url(url).host in {"localhost", "127.0.0.1", "::1"}
    schema = "provider_network_repo_" + uuid4().hex
    admin = create_async_engine(url)
    try:
        async with admin.begin() as conn:
            await conn.execute(CreateSchema(schema))
            await conn.execute(text(f'SET LOCAL search_path TO "{schema}"'))
            for statement in filter(None, (s.strip() for s in _PARENTS.split(";"))):
                await conn.execute(text(statement))
            for table in (
                ProviderOrganisationModel.__table__,
                ProviderAffiliationModel.__table__,
            ):
                await conn.run_sync(table.create)
            await conn.execute(text("INSERT INTO tenants (id) VALUES ('tenant-a'), ('tenant-b')"))
            await conn.execute(
                text(
                    "INSERT INTO providers (id, tenant_id) VALUES "
                    "('prov-a', 'tenant-a'), ('prov-b', 'tenant-b')"
                )
            )
            await conn.execute(
                text(
                    "INSERT INTO provider_organisations "
                    "(id, tenant_id, name, is_active, approval_status, created_at, updated_at) "
                    "VALUES ('org-a', 'tenant-a', 'Firm A', true, 'Approved', now(), now())"
                )
            )
            await conn.execute(
                text(
                    "INSERT INTO provider_affiliations "
                    "(id, tenant_id, provider_id, organisation_id, valid_from, valid_until, "
                    " created_at, updated_at) VALUES "
                    "('aff-1','tenant-a','prov-a','org-a',DATE '2026-01-01',DATE '2026-07-01',"
                    " now(), now()),"
                    "('aff-open','tenant-a','prov-a','org-a',DATE '2027-01-01',NULL,"
                    " now(), now())"
                )
            )
        engine = create_async_engine(url, connect_args={"server_settings": {"search_path": schema}})
        yield async_sessionmaker(engine, expire_on_commit=False)
        await engine.dispose()
    finally:
        async with admin.begin() as conn:
            await conn.execute(DropSchema(schema, cascade=True))
        await admin.dispose()


async def _resolve(session_factory, *, tenant=TENANT_A, provider=PROV_A, at, affiliation=AFF):
    async with session_factory() as session:
        repo = ProviderAffiliationRepositoryImpl(session)
        return await repo.get_valid_affiliation(tenant, affiliation, provider_id=provider, at=at)


def _kampala(year, month, day, hour=12, minute=0) -> datetime:
    return datetime(year, month, day, hour, minute, tzinfo=KAMPALA)


class TestAgent1AcceptanceCases:
    async def test_different_practitioner_same_tenant_returns_none(self, session_factory):
        assert (
            await _resolve(session_factory, provider=ProviderId("prov-b"), at=_kampala(2026, 3, 1))
            is None
        )

    async def test_different_tenant_returns_none(self, session_factory):
        assert await _resolve(session_factory, tenant=TENANT_B, at=_kampala(2026, 3, 1)) is None

    async def test_at_valid_from_resolves(self, session_factory):
        result = await _resolve(session_factory, at=_kampala(2026, 1, 1))
        assert result is not None
        assert result.id == AFF

    async def test_at_valid_until_does_not_resolve(self, session_factory):
        """End-exclusive, per decision 1."""
        assert await _resolve(session_factory, at=_kampala(2026, 7, 1)) is None

    async def test_open_ended_resolves_for_any_later_moment(self, session_factory):
        result = await _resolve(
            session_factory,
            affiliation=ProviderAffiliationId("aff-open"),
            at=_kampala(2099, 5, 5),
        )
        assert result is not None

    async def test_unknown_affiliation_returns_none_and_does_not_raise(self, session_factory):
        assert (
            await _resolve(
                session_factory, affiliation=ProviderAffiliationId("nope"), at=_kampala(2026, 3, 1)
            )
            is None
        )


class TestBoundaryTimezone:
    async def test_the_day_is_taken_in_kampala_not_utc(self, session_factory):
        """2026-06-30T22:30Z is 2026-07-01 in Kampala, so it falls outside.

        Evaluated in UTC this would resolve, which is exactly the divergence the
        agreed single timezone prevents.
        """
        utc_moment = datetime(2026, 6, 30, 22, 30, tzinfo=UTC)
        assert utc_moment.astimezone(KAMPALA).date() == date(2026, 7, 1)
        assert await _resolve(session_factory, at=utc_moment) is None

    async def test_the_last_covered_moment_resolves(self, session_factory):
        result = await _resolve(session_factory, at=_kampala(2026, 6, 30, 23, 59))
        assert result is not None

    async def test_a_naive_datetime_is_refused(self, session_factory):
        with pytest.raises(ValueError):
            await _resolve(session_factory, at=datetime(2026, 3, 1, 12, 0))


class TestOverlapDetection:
    async def _overlaps(self, session_factory, valid_from, valid_until):
        async with session_factory() as session:
            repo = ProviderAffiliationRepositoryImpl(session)
            return await repo.find_overlapping(
                TENANT_A, PROV_A, ORG, valid_from=valid_from, valid_until=valid_until
            )

    async def test_an_adjacent_interval_does_not_overlap(self, session_factory):
        found = await self._overlaps(session_factory, date(2026, 7, 1), date(2026, 12, 1))
        assert [a.id.value for a in found] == []

    async def test_an_interval_ending_at_the_start_does_not_overlap(self, session_factory):
        found = await self._overlaps(session_factory, date(2025, 1, 1), date(2026, 1, 1))
        assert found == []

    async def test_a_one_day_intrusion_overlaps(self, session_factory):
        found = await self._overlaps(session_factory, date(2026, 6, 30), date(2026, 12, 1))
        assert [a.id.value for a in found] == ["aff-1"]

    async def test_an_open_ended_new_interval_catches_the_later_affiliation(self, session_factory):
        found = await self._overlaps(session_factory, date(2026, 8, 1), None)
        assert [a.id.value for a in found] == ["aff-open"]

    async def test_a_contained_interval_overlaps(self, session_factory):
        found = await self._overlaps(session_factory, date(2026, 2, 1), date(2026, 3, 1))
        assert [a.id.value for a in found] == ["aff-1"]


class TestOrganisationLookup:
    async def test_cross_tenant_organisation_returns_none(self, session_factory):
        async with session_factory() as session:
            repo = ProviderOrganisationRepositoryImpl(session)
            assert await repo.get_organisation(TENANT_B, ORG) is None

    async def test_same_tenant_organisation_reports_both_facts(self, session_factory):
        async with session_factory() as session:
            repo = ProviderOrganisationRepositoryImpl(session)
            org = await repo.get_organisation(TENANT_A, ORG)
        assert org is not None
        assert org.is_active is True
        assert org.approval_status.value == "Approved"
        assert org.can_deliver() is True

    async def test_listing_returns_the_full_matching_total(self, session_factory):
        async with session_factory() as session:
            repo = ProviderOrganisationRepositoryImpl(session)
            items, total = await repo.list_organisations(TENANT_A, limit=1, offset=0)
        assert len(items) == 1
        assert total == 1

    async def test_listing_is_tenant_scoped(self, session_factory):
        async with session_factory() as session:
            repo = ProviderOrganisationRepositoryImpl(session)
            items, total = await repo.list_organisations(TENANT_B)
        assert (items, total) == ([], 0)
