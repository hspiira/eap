"""The delivery record is aggregated in SQL, over the whole dataset.

The organisation breakdown resolves through the affiliation each session
stored. Decision 2 forbids reattributing delivered sessions when a
practitioner's affiliations change, so a newer affiliation must leave an older
session counted against the organisation it was delivered under.

Run with MEMBER_TEST_DATABASE_URL pointing at local PostgreSQL.
"""

from datetime import UTC, date, datetime
from uuid import uuid4

import pytest_asyncio
from sqlalchemy import text
from sqlalchemy.engine import make_url
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine
from sqlalchemy.pool import NullPool
from sqlalchemy.schema import CreateSchema, DropSchema

from app.domain.enums import (
    AccreditationStatus,
    BaseStatus,
    PanelStatus,
    ProviderIdentityProvenance,
    ProviderTier,
    SessionDeliveryContext,
    SessionStatus,
    SubscriptionTier,
    TenantStatus,
    UgandaRegion,
)
from app.domain.enums.provider_network import OrganisationApprovalStatus
from app.domain.value_objects.core import ProviderId, TenantId
from app.infrastructure.models.base import Base
from app.infrastructure.models.provider_affiliation_model import ProviderAffiliationModel
from app.infrastructure.models.provider_model import ProviderModel
from app.infrastructure.models.provider_organisation_model import ProviderOrganisationModel
from app.infrastructure.models.service_session_model import ServiceSessionModel
from app.infrastructure.models.tenant_model import TenantModel
from app.infrastructure.repositories.service_session_repository import (
    ServiceSessionRepositoryImpl,
)
from app.shared.utils.datetime import utc_now
from tests.integration._database_url import require_local_database

TENANT = "tenant-delivery"
PROVIDER = "provider-delivery"
OTHER_PROVIDER = "provider-delivery-other"
ORGANISATION_A = "org-delivery-a"
ORGANISATION_B = "org-delivery-b"
AFFILIATION_A = "aff-delivery-a"
AFFILIATION_B = "aff-delivery-b"


def _provider_model(provider_id: str, name: str, now: datetime) -> ProviderModel:
    return ProviderModel(
        id=provider_id,
        tenant_id=TENANT,
        user_id=None,
        display_name=name,
        identity_provenance=ProviderIdentityProvenance.OWNED,
        status=BaseStatus.ACTIVE,
        provider_profile={
            "tier": ProviderTier.T1.value,
            "region": UgandaRegion.CENTRAL.value,
            "accreditation_status": AccreditationStatus.ACCREDITED.value,
            "panel_status": PanelStatus.ACTIVE.value,
        },
        created_at=now,
        updated_at=now,
    )


def _organisation_model(
    organisation_id: str, name: str, now: datetime
) -> ProviderOrganisationModel:
    return ProviderOrganisationModel(
        id=organisation_id,
        tenant_id=TENANT,
        name=name,
        is_active=True,
        approval_status=OrganisationApprovalStatus.APPROVED,
        created_at=now,
        updated_at=now,
    )


@pytest_asyncio.fixture
async def db():
    url = make_url(require_local_database("MEMBER_TEST_DATABASE_URL"))
    schema = "delivery_" + uuid4().hex
    admin = create_async_engine(url, poolclass=NullPool)
    async with admin.begin() as connection:
        await connection.execute(CreateSchema(schema))
    engine = create_async_engine(
        url, poolclass=NullPool, connect_args={"server_settings": {"search_path": schema}}
    )
    async with engine.begin() as connection:
        await connection.run_sync(Base.metadata.create_all)
    sessions = async_sessionmaker(engine, expire_on_commit=False)

    now = utc_now()
    async with sessions() as session:
        session.add(
            TenantModel(
                id=TENANT,
                name="Delivery tenant",
                code="delv",
                settings={},
                status=TenantStatus.ACTIVE,
                subscription_tier=SubscriptionTier.FREE,
            )
        )
        await session.commit()
    async with sessions() as session:
        session.add(_provider_model(PROVIDER, "Amina Okello", now))
        session.add(_provider_model(OTHER_PROVIDER, "Brian Wamala", now))
        session.add(_organisation_model(ORGANISATION_A, "Kampala Counselling Partners", now))
        session.add(_organisation_model(ORGANISATION_B, "Entebbe Wellbeing Group", now))
        await session.commit()
    async with sessions() as session:
        await session.execute(
            text(
                "INSERT INTO clients (id, tenant_id, name, code, status, contact_info,"
                " is_verified, created_at, updated_at)"
                " VALUES ('client-1', :tenant, 'Delivery Client', 'DELV', 'Active',"
                " '{}', true, now(), now())"
            ),
            {"tenant": TENANT},
        )
        await session.execute(
            text(
                "INSERT INTO eligible_members (id, tenant_id, client_id, employer_member_id,"
                " relation, status, created_at, updated_at)"
                " VALUES ('member-1', :tenant, 'client-1', 'EMP-1', 'Employee', 'Active',"
                " now(), now())"
            ),
            {"tenant": TENANT},
        )
        await session.commit()
    async with sessions() as session:
        session.add(
            ProviderAffiliationModel(
                id=AFFILIATION_A,
                tenant_id=TENANT,
                provider_id=PROVIDER,
                organisation_id=ORGANISATION_A,
                valid_from=date(2023, 1, 1),
                valid_until=date(2024, 12, 31),
                created_at=now,
                updated_at=now,
            )
        )
        await session.commit()
    try:
        yield sessions
    finally:
        await engine.dispose()
        async with admin.begin() as connection:
            await connection.execute(DropSchema(schema, cascade=True))
        await admin.dispose()


async def _add_affiliation_b(db) -> None:
    """The practitioner's later, and current, organisation."""
    now = utc_now()
    async with db() as session:
        session.add(
            ProviderAffiliationModel(
                id=AFFILIATION_B,
                tenant_id=TENANT,
                provider_id=PROVIDER,
                organisation_id=ORGANISATION_B,
                valid_from=date(2025, 1, 1),
                valid_until=None,
                created_at=now,
                updated_at=now,
            )
        )
        await session.commit()


async def _add_session(
    db,
    session_id: str,
    scheduled_at: datetime,
    *,
    delivery_context: SessionDeliveryContext = SessionDeliveryContext.UNKNOWN,
    affiliation_id: str | None = None,
    provider_id: str = PROVIDER,
) -> None:
    now = utc_now()
    async with db() as session:
        session.add(
            ServiceSessionModel(
                id=session_id,
                tenant_id=TENANT,
                service_id="svc-1",
                provider_id=provider_id,
                client_id="client-1",
                member_id="member-1",
                scheduled_at=scheduled_at,
                delivery_context=delivery_context,
                provider_affiliation_id=affiliation_id,
                status=SessionStatus.COMPLETED,
                reschedule_count=0,
                created_at=now,
                updated_at=now,
            )
        )
        await session.commit()


async def _add_organisation_session(
    db, session_id: str, scheduled_at: datetime, affiliation_id: str
) -> None:
    await _add_session(
        db,
        session_id,
        scheduled_at,
        delivery_context=SessionDeliveryContext.ORGANISATION,
        affiliation_id=affiliation_id,
    )


async def _stats(db, provider_id: str = PROVIDER):
    async with db() as session:
        repo = ServiceSessionRepositoryImpl(session)
        return await repo.provider_delivery_stats(TenantId(TENANT), ProviderId(provider_id))


class TestTotals:
    async def test_a_practitioner_with_no_sessions_reports_nothing(self, db):
        stats = await _stats(db)
        assert stats.total_sessions == 0
        assert stats.first_session_at is None
        assert stats.last_session_at is None
        assert stats.by_delivery_context == {}
        assert stats.by_organisation == []

    async def test_the_total_spans_the_whole_record_not_a_page(self, db):
        for index in range(25):
            await _add_session(db, f"s-{index}", datetime(2024, 3, 1, 9, 0, tzinfo=UTC))
        stats = await _stats(db)
        assert stats.total_sessions == 25

    async def test_the_bounds_are_the_earliest_and_latest_scheduled_instants(self, db):
        await _add_session(db, "s-mid", datetime(2024, 6, 1, 10, 0, tzinfo=UTC))
        await _add_session(db, "s-first", datetime(2023, 2, 3, 8, 30, tzinfo=UTC))
        await _add_session(
            db,
            "s-last",
            datetime(2025, 9, 9, 16, 0, tzinfo=UTC),
            delivery_context=SessionDeliveryContext.DIRECT,
        )
        stats = await _stats(db)
        assert stats.first_session_at == datetime(2023, 2, 3, 8, 30, tzinfo=UTC)
        assert stats.last_session_at == datetime(2025, 9, 9, 16, 0, tzinfo=UTC)

    async def test_a_soft_deleted_session_is_not_counted(self, db):
        await _add_session(db, "s-kept", datetime(2024, 6, 1, 10, 0, tzinfo=UTC))
        await _add_session(db, "s-gone", datetime(2025, 6, 1, 10, 0, tzinfo=UTC))
        async with db() as session:
            await session.execute(
                text("UPDATE service_sessions SET deleted_at = now() WHERE id = 's-gone'")
            )
            await session.commit()
        stats = await _stats(db)
        assert stats.total_sessions == 1
        assert stats.last_session_at == datetime(2024, 6, 1, 10, 0, tzinfo=UTC)

    async def test_another_practitioners_sessions_are_not_counted(self, db):
        await _add_session(
            db, "s-other", datetime(2024, 6, 1, 10, 0, tzinfo=UTC), provider_id=OTHER_PROVIDER
        )
        assert (await _stats(db)).total_sessions == 0
        assert (await _stats(db, OTHER_PROVIDER)).total_sessions == 1


class TestDeliveryContext:
    async def test_each_context_carries_its_own_count(self, db):
        await _add_session(db, "s-u1", datetime(2024, 1, 1, 9, 0, tzinfo=UTC))
        await _add_session(db, "s-u2", datetime(2024, 1, 2, 9, 0, tzinfo=UTC))
        await _add_session(
            db,
            "s-d1",
            datetime(2024, 1, 3, 9, 0, tzinfo=UTC),
            delivery_context=SessionDeliveryContext.DIRECT,
        )
        await _add_organisation_session(
            db, "s-o1", datetime(2024, 1, 4, 9, 0, tzinfo=UTC), AFFILIATION_A
        )
        stats = await _stats(db)
        assert stats.by_delivery_context == {
            SessionDeliveryContext.UNKNOWN: 2,
            SessionDeliveryContext.DIRECT: 1,
            SessionDeliveryContext.ORGANISATION: 1,
        }

    async def test_a_context_with_no_sessions_is_omitted(self, db):
        await _add_session(db, "s-u1", datetime(2024, 1, 1, 9, 0, tzinfo=UTC))
        stats = await _stats(db)
        assert stats.by_delivery_context == {SessionDeliveryContext.UNKNOWN: 1}


class TestOrganisationBreakdown:
    async def test_direct_delivery_appears_in_no_organisation(self, db):
        await _add_session(
            db,
            "s-direct",
            datetime(2024, 1, 1, 9, 0, tzinfo=UTC),
            delivery_context=SessionDeliveryContext.DIRECT,
        )
        assert (await _stats(db)).by_organisation == []

    async def test_a_later_affiliation_does_not_reattribute_delivered_sessions(self, db):
        """Decision 2: the session's stored affiliation decides, not the roster today."""
        await _add_organisation_session(
            db, "s-under-a", datetime(2024, 5, 1, 9, 0, tzinfo=UTC), AFFILIATION_A
        )

        await _add_affiliation_b(db)

        stats = await _stats(db)
        assert [(row.organisation_id, row.session_count) for row in stats.by_organisation] == [
            (ORGANISATION_A, 1)
        ]
        assert stats.by_organisation[0].organisation_name == "Kampala Counselling Partners"

    async def test_each_affiliation_counts_against_its_own_organisation(self, db):
        await _add_affiliation_b(db)
        await _add_organisation_session(
            db, "s-a1", datetime(2024, 5, 1, 9, 0, tzinfo=UTC), AFFILIATION_A
        )
        await _add_organisation_session(
            db, "s-b1", datetime(2025, 5, 1, 9, 0, tzinfo=UTC), AFFILIATION_B
        )
        await _add_organisation_session(
            db, "s-b2", datetime(2025, 6, 1, 9, 0, tzinfo=UTC), AFFILIATION_B
        )

        stats = await _stats(db)

        assert [(row.organisation_id, row.session_count) for row in stats.by_organisation] == [
            (ORGANISATION_B, 2),
            (ORGANISATION_A, 1),
        ], "the busiest organisation comes first"
