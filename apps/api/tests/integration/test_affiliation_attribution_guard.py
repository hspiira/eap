"""Narrowing an affiliation must not silently orphan completed attribution.

Decision 2 requires a date change that would stop covering an already-completed
session to be rejected or carried in an explicit correction. This is the
enforcement side: the guard reports the sessions such a change would orphan.

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
from app.domain.value_objects.core import TenantId
from app.domain.value_objects.provider_network import ProviderAffiliationId
from app.infrastructure.models.base import Base
from app.infrastructure.models.provider_affiliation_model import ProviderAffiliationModel
from app.infrastructure.models.provider_model import ProviderModel
from app.infrastructure.models.provider_organisation_model import ProviderOrganisationModel
from app.infrastructure.models.service_session_model import ServiceSessionModel
from app.infrastructure.models.tenant_model import TenantModel
from app.infrastructure.repositories.affiliation_attribution_guard import (
    SqlAffiliationAttributionGuard,
)
from app.shared.utils.datetime import utc_now
from tests.integration._database_url import require_local_database

TENANT = "tenant-attribution"
PROVIDER = "provider-attribution"
ORGANISATION = "org-attribution"
AFFILIATION = "aff-attribution"


@pytest_asyncio.fixture
async def db():
    url = make_url(require_local_database("MEMBER_TEST_DATABASE_URL"))
    schema = "attribution_" + uuid4().hex
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
                name="Attribution tenant",
                code="attrb",
                settings={},
                status=TenantStatus.ACTIVE,
                subscription_tier=SubscriptionTier.FREE,
            )
        )
        await session.commit()
    async with sessions() as session:
        session.add(
            ProviderModel(
                id=PROVIDER,
                tenant_id=TENANT,
                user_id=None,
                display_name="Amina Okello",
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
        )
        session.add(
            ProviderOrganisationModel(
                id=ORGANISATION,
                tenant_id=TENANT,
                name="Kampala Counselling Partners",
                is_active=True,
                approval_status=OrganisationApprovalStatus.APPROVED,
                created_at=now,
                updated_at=now,
            )
        )
        await session.commit()
    async with sessions() as session:
        # The member's client, which service_sessions now points at directly.
        await session.execute(
            text(
                "INSERT INTO clients (id, tenant_id, name, code, status, contact_info,"
                " is_verified, created_at, updated_at)"
                " VALUES ('client-1', :tenant, 'Attribution Client', 'ATTR', 'Active',"
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
                id=AFFILIATION,
                tenant_id=TENANT,
                provider_id=PROVIDER,
                organisation_id=ORGANISATION,
                valid_from=date(2023, 1, 1),
                valid_until=date(2026, 1, 1),
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


async def _add_session(db, session_id: str, scheduled_at: datetime, status: SessionStatus) -> None:
    now = utc_now()
    async with db() as session:
        session.add(
            ServiceSessionModel(
                id=session_id,
                tenant_id=TENANT,
                service_id="svc-1",
                provider_id=PROVIDER,
                client_id="client-1",
                member_id="member-1",
                scheduled_at=scheduled_at,
                delivery_context=SessionDeliveryContext.ORGANISATION,
                provider_affiliation_id=AFFILIATION,
                status=status,
                reschedule_count=0,
                created_at=now,
                updated_at=now,
            )
        )
        await session.commit()


async def _orphaned(db, new_valid_until: date | None) -> list[str]:
    async with db() as session:
        guard = SqlAffiliationAttributionGuard(session)
        return list(
            await guard.sessions_orphaned_by(
                TenantId(TENANT),
                ProviderAffiliationId(AFFILIATION),
                new_valid_until=new_valid_until,
            )
        )


class TestNarrowing:
    async def test_a_completed_session_outside_the_new_interval_is_reported(self, db):
        await _add_session(
            db, "s-late", datetime(2025, 6, 1, 10, 0, tzinfo=UTC), SessionStatus.COMPLETED
        )
        assert await _orphaned(db, date(2025, 1, 1)) == ["s-late"]

    async def test_a_completed_session_still_inside_the_new_interval_is_not(self, db):
        await _add_session(
            db, "s-early", datetime(2023, 6, 1, 10, 0, tzinfo=UTC), SessionStatus.COMPLETED
        )
        assert await _orphaned(db, date(2025, 1, 1)) == []

    async def test_the_new_end_date_itself_is_outside_because_the_interval_is_end_exclusive(
        self, db
    ):
        await _add_session(
            db, "s-boundary", datetime(2025, 1, 1, 10, 0, tzinfo=UTC), SessionStatus.COMPLETED
        )
        assert await _orphaned(db, date(2025, 1, 1)) == ["s-boundary"]

    async def test_a_scheduled_session_is_not_reported(self, db):
        """Only completed delivery is a fact the change would rewrite."""
        await _add_session(
            db, "s-future", datetime(2025, 6, 1, 10, 0, tzinfo=UTC), SessionStatus.SCHEDULED
        )
        assert await _orphaned(db, date(2025, 1, 1)) == []

    async def test_the_day_is_taken_in_kampala_not_utc(self, db):
        """22:30Z on 31 December is already 1 January in Kampala."""
        await _add_session(
            db, "s-midnight", datetime(2024, 12, 31, 22, 30, tzinfo=UTC), SessionStatus.COMPLETED
        )
        assert await _orphaned(db, date(2025, 1, 1)) == ["s-midnight"]


class TestSafeChanges:
    async def test_widening_never_orphans_anything(self, db):
        await _add_session(
            db, "s-late", datetime(2025, 6, 1, 10, 0, tzinfo=UTC), SessionStatus.COMPLETED
        )
        assert await _orphaned(db, date(2027, 1, 1)) == []

    async def test_reopening_to_open_ended_never_orphans_anything(self, db):
        await _add_session(
            db, "s-late", datetime(2025, 6, 1, 10, 0, tzinfo=UTC), SessionStatus.COMPLETED
        )
        assert await _orphaned(db, None) == []

    async def test_a_session_on_another_affiliation_is_not_reported(self, db):
        await _add_session(
            db, "s-other", datetime(2025, 6, 1, 10, 0, tzinfo=UTC), SessionStatus.COMPLETED
        )
        async with db() as session:
            await session.execute(
                text(
                    "UPDATE service_sessions SET provider_affiliation_id = NULL,"
                    " delivery_context = 'Direct' WHERE id = 's-other'"
                )
            )
            await session.commit()
        assert await _orphaned(db, date(2025, 1, 1)) == []
