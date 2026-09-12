"""Dashboard aggregate endpoint.

Seeds a small tenant directly through the models and checks every block of
the response: KPI counts, the zero-filled monthly series, the category and
client groupings, the import backlog scoped to the latest non-abandoned
batch, and the derived data-quality queues. A second tenant's data proves
the scoping.
"""

from datetime import UTC, datetime, timedelta

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.enums import (
    BaseStatus,
    EligibilityStatus,
    MemberRelation,
    SessionAttendance,
    SessionCategory,
    SessionClinicalStatus,
    SessionStatus,
    SessionType,
)
from app.domain.enums.contract import ContractStatus, PaymentFrequency, PaymentStatus
from app.domain.enums.crisis import CriticalIncidentSeverity, CriticalIncidentStatus
from app.domain.enums.provider_network import ImportBatchStatus, ImportRowOutcome
from app.infrastructure.models.client_model import ClientModel
from app.infrastructure.models.contract_model import ContractModel
from app.infrastructure.models.critical_incident_model import CriticalIncidentModel
from app.infrastructure.models.eligible_member_model import EligibleMemberModel
from app.infrastructure.models.provider_model import ProviderModel
from app.infrastructure.models.service_model import ServiceModel
from app.infrastructure.models.service_session_model import ServiceSessionModel
from app.infrastructure.models.session_import_model import (
    SessionImportBatchModel,
    SessionImportRowModel,
)
from app.infrastructure.models.tenant_model import TenantModel
from app.shared.utils.datetime import utc_now
from app.shared.utils.generators import generate_cuid

TENANT = "tenant-dash-1"
OTHER_TENANT = "tenant-dash-2"


def _tenant(tenant_id: str) -> TenantModel:
    return TenantModel(id=tenant_id, name=tenant_id, code=tenant_id, settings={})


def _client_row(tenant_id: str, client_id: str, name: str, code: str) -> ClientModel:
    return ClientModel(
        id=client_id,
        tenant_id=tenant_id,
        name=name,
        code=code,
        contact_info={},
        status=BaseStatus.PENDING,
    )


def _session(
    tenant_id: str,
    client_id: str,
    provider_id: str,
    *,
    days_ago: int = 0,
    at: datetime | None = None,
    service_id: str = "svc-talk",
    session_type: SessionType | None = SessionType.PHYSICAL,
    status: SessionStatus = SessionStatus.COMPLETED,
    category: SessionCategory | None = SessionCategory.GROUP,
    clinical_outcome: SessionClinicalStatus | None = SessionClinicalStatus.COMPLETED,
    rate_ugx: int | None = 100_000,
    deleted: bool = False,
) -> ServiceSessionModel:
    now = utc_now()
    return ServiceSessionModel(
        id=generate_cuid(),
        tenant_id=tenant_id,
        service_id=service_id,
        provider_id=provider_id,
        client_id=client_id,
        scheduled_at=at if at is not None else now - timedelta(days=days_ago),
        status=status,
        session_type=session_type,
        attendance=SessionAttendance.COMPANY_WIDE,
        category=category,
        clinical_outcome=clinical_outcome,
        rate_ugx=rate_ugx,
        deleted_at=now if deleted else None,
    )


def _member(
    tenant_id: str, client_id: str, index: int, status: EligibilityStatus
) -> EligibleMemberModel:
    return EligibleMemberModel(
        id=generate_cuid(),
        tenant_id=tenant_id,
        client_id=client_id,
        employer_member_id=f"emp-{index}",
        relation=MemberRelation.EMPLOYEE,
        status=status,
    )


def _batch(tenant_id: str, batch_id: str, status: ImportBatchStatus) -> SessionImportBatchModel:
    return SessionImportBatchModel(
        id=batch_id,
        tenant_id=tenant_id,
        source_system="xlsx",
        file_name="sessions.csv",
        file_hash=batch_id,
        staged_by="user-1",
        status=status,
        row_count=4,
    )


def _row(
    tenant_id: str, batch_id: str, number: int, outcome: ImportRowOutcome
) -> SessionImportRowModel:
    return SessionImportRowModel(
        id=generate_cuid(),
        tenant_id=tenant_id,
        batch_id=batch_id,
        row_number=number,
        replay_key=f"{batch_id}-{number}",
        outcome=outcome,
    )


async def _seed(db: AsyncSession) -> None:
    provider = "prov-dash-1"
    db.add_all([_tenant(TENANT), _tenant(OTHER_TENANT)])
    await db.flush()
    db.add_all(
        [
            _client_row(TENANT, "cl-dash-a", "Alpha Bank", "ALPHA"),
            _client_row(TENANT, "cl-dash-b", "Beta Ltd", "BETA"),
            _client_row(OTHER_TENANT, "cl-dash-x", "Other Tenant Co", "OTHER"),
        ]
    )
    db.add_all(
        [
            ProviderModel(
                id=provider, tenant_id=TENANT, display_name="Counsellor", status=BaseStatus.ACTIVE
            ),
            ProviderModel(
                id="prov-dash-2",
                tenant_id=TENANT,
                display_name="Pending One",
                status=BaseStatus.PENDING,
            ),
            ProviderModel(
                id="prov-dash-x",
                tenant_id=OTHER_TENANT,
                display_name="Other",
                status=BaseStatus.PENDING,
            ),
        ]
    )
    db.add_all(
        [
            ServiceModel(id="svc-talk", tenant_id=TENANT, name="Health Talk"),
            ServiceModel(id="svc-couns", tenant_id=TENANT, name="Counselling"),
        ]
    )
    await db.flush()

    db.add_all(
        [
            # Recent window: three completed for Alpha, one for Beta.
            _session(TENANT, "cl-dash-a", provider, days_ago=5),
            _session(
                TENANT,
                "cl-dash-a",
                provider,
                days_ago=10,
                category=SessionCategory.FAMILY,
                session_type=SessionType.ONLINE,
            ),
            _session(
                TENANT,
                "cl-dash-a",
                provider,
                days_ago=20,
                service_id="svc-couns",
                session_type=None,
                clinical_outcome=None,
                rate_ugx=None,
            ),
            _session(TENANT, "cl-dash-b", provider, days_ago=30),
            # Prior 90-day window.
            _session(TENANT, "cl-dash-a", provider, days_ago=100),
            # Excluded: cancelled, soft-deleted, other tenant.
            _session(TENANT, "cl-dash-a", provider, days_ago=6, status=SessionStatus.CANCELLED),
            _session(TENANT, "cl-dash-a", provider, days_ago=7, deleted=True),
            _session(OTHER_TENANT, "cl-dash-x", "prov-dash-x", days_ago=5),
        ]
    )
    db.add_all(
        [
            _member(TENANT, "cl-dash-a", 1, EligibilityStatus.ACTIVE),
            _member(TENANT, "cl-dash-a", 2, EligibilityStatus.ACTIVE),
            _member(TENANT, "cl-dash-a", 3, EligibilityStatus.TERMINATED),
            _member(OTHER_TENANT, "cl-dash-x", 4, EligibilityStatus.ACTIVE),
        ]
    )
    db.add_all(
        [
            _batch(TENANT, "batch-dash-old", ImportBatchStatus.ABANDONED),
            _batch(TENANT, "batch-dash-new", ImportBatchStatus.APPLIED),
        ]
    )
    await db.flush()
    db.add_all(
        [
            _row(TENANT, "batch-dash-old", 1, ImportRowOutcome.UNRESOLVED_MEMBER),
            _row(TENANT, "batch-dash-new", 1, ImportRowOutcome.ACCEPTED),
            _row(TENANT, "batch-dash-new", 2, ImportRowOutcome.UNRESOLVED_MEMBER),
            _row(TENANT, "batch-dash-new", 3, ImportRowOutcome.UNRESOLVED_MEMBER),
            _row(TENANT, "batch-dash-new", 4, ImportRowOutcome.MISSING_PRACTITIONER),
            _row(TENANT, "batch-dash-new", 5, ImportRowOutcome.DUPLICATE),
        ]
    )
    await db.commit()


@pytest.mark.asyncio
async def test_dashboard_aggregates_one_tenant(client: AsyncClient, db_session: AsyncSession):
    await _seed(db_session)

    response = await client.get("/dashboard", params={"tenant_id": TENANT, "range": "last_90d"})
    assert response.status_code == 200
    body = response.json()

    assert body["range"]["preset"] == "last_90d"
    assert body["range"]["granularity"] == "week"

    kpis = body["kpis"]
    assert kpis["sessions"] == 4
    assert kpis["sessions_prior"] == 1
    assert kpis["clients_served"] == 2
    assert kpis["covered_members"] == 2
    assert kpis["clients_with_roster"] == 1
    assert kpis["clients_total"] == 2
    assert kpis["import_backlog"] == 3

    series = body["sessions_series"]
    assert sum(p["total"] for p in series) == 4
    # The delivery split is carried per bucket, and an unrecorded type stays
    # its own band rather than being folded into either.
    assert sum(p["physical"] for p in series) == 2
    assert sum(p["online"] for p in series) == 1
    assert sum(p["unknown"] for p in series) == 1

    categories = {c["category"]: c["total"] for c in body["sessions_by_category"]}
    assert categories == {"Group": 3, "Family": 1}

    top = [(c["client_name"], c["total"]) for c in body["top_clients"]]
    assert top == [("Alpha Bank", 3), ("Beta Ltd", 1)]

    services = {
        s["service_name"]: (s["total"], s["prior_total"], s["change_pct"])
        for s in body["trending_services"]
    }
    assert services["Health Talk"] == (3, 1, 200.0)
    # No prior sessions means no percentage can be stated, not a 100% rise.
    assert services["Counselling"] == (1, 0, None)

    # The batch composition and its per-outcome queues are not reported: a
    # staged batch describes file imports only, so a session entered on the
    # form contributes nothing to it. The backlog total above is what remains.
    assert "import_queues" not in body
    assert "import_batch" not in body

    quality = body["data_quality"]
    assert quality["sessions_missing_outcome"] == 1
    assert quality["sessions_missing_rate"] == 1
    assert quality["clients_without_roster"] == 1
    assert quality["providers_pending"] == 1


@pytest.mark.asyncio
async def test_dashboard_range_presets_rebucket(client: AsyncClient, db_session: AsyncSession):
    """A narrower window re-scopes every flow figure and re-buckets the series."""
    await _seed(db_session)

    response = await client.get("/dashboard", params={"tenant_id": TENANT, "range": "last_30d"})
    body = response.json()
    assert body["range"]["granularity"] == "day"
    assert len(body["sessions_series"]) == 31
    # days_ago 5, 10, 20 fall inside 30 days; 30 and 100 do not.
    assert body["kpis"]["sessions"] == 3
    assert sum(p["total"] for p in body["sessions_series"]) == 3

    half = await client.get("/dashboard", params={"tenant_id": TENANT, "range": "last_180d"})
    assert half.json()["range"]["granularity"] == "month"
    assert half.json()["kpis"]["sessions"] == 5


@pytest.mark.asyncio
async def test_dashboard_custom_range(client: AsyncClient, db_session: AsyncSession):
    await _seed(db_session)
    start = (utc_now() - timedelta(days=15)).date().isoformat()

    response = await client.get(
        "/dashboard", params={"tenant_id": TENANT, "range": "custom", "start": start}
    )
    assert response.status_code == 200
    body = response.json()
    assert body["range"]["preset"] == "custom"
    # Only days_ago 5 and 10 fall inside the last 15 days.
    assert body["kpis"]["sessions"] == 2


@pytest.mark.asyncio
async def test_dashboard_custom_range_needs_a_start(client: AsyncClient, db_session: AsyncSession):
    db_session.add(_tenant(TENANT))
    await db_session.commit()

    response = await client.get("/dashboard", params={"tenant_id": TENANT, "range": "custom"})
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_dashboard_empty_tenant(client: AsyncClient, db_session: AsyncSession):
    db_session.add(_tenant(TENANT))
    await db_session.commit()

    response = await client.get("/dashboard", params={"tenant_id": TENANT})
    assert response.status_code == 200
    body = response.json()
    assert body["kpis"]["clients_total"] == 0
    assert body["kpis"]["import_backlog"] == 0
    assert body["trending_services"] == []
    assert all(p["total"] == 0 for p in body["sessions_series"])


async def _seed_across_years(db: AsyncSession) -> None:
    """One tenant, one client, sessions in three separate calendar years."""
    db.add(_tenant(TENANT))
    await db.flush()
    db.add(_client_row(TENANT, "cl-yr", "Yearly Co", "YEAR"))
    db.add(
        ProviderModel(
            id="prov-yr", tenant_id=TENANT, display_name="Counsellor", status=BaseStatus.ACTIVE
        )
    )
    db.add(ServiceModel(id="svc-talk", tenant_id=TENANT, name="Health Talk"))
    await db.flush()
    db.add_all(
        [
            _session(TENANT, "cl-yr", "prov-yr", at=datetime(2023, 6, 1, 10, tzinfo=UTC)),
            _session(TENANT, "cl-yr", "prov-yr", at=datetime(2024, 3, 4, 10, tzinfo=UTC)),
            _session(TENANT, "cl-yr", "prov-yr", at=datetime(2024, 8, 9, 10, tzinfo=UTC)),
            _session(TENANT, "cl-yr", "prov-yr", at=datetime(2025, 2, 2, 10, tzinfo=UTC)),
        ]
    )
    await db.commit()


@pytest.mark.asyncio
async def test_dashboard_offers_only_years_that_have_sessions(
    client: AsyncClient, db_session: AsyncSession
):
    await _seed_across_years(db_session)

    response = await client.get("/dashboard", params={"tenant_id": TENANT, "range": "this_year"})

    assert response.status_code == 200, response.text
    years = response.json()["session_years"]
    assert years == sorted(years, reverse=True)
    assert min(years) == 2023, years
    assert 2022 not in years


@pytest.mark.asyncio
async def test_dashboard_with_no_sessions_offers_no_years(
    client: AsyncClient, db_session: AsyncSession
):
    db_session.add(_tenant(TENANT))
    await db_session.commit()

    response = await client.get("/dashboard", params={"tenant_id": TENANT})

    assert response.status_code == 200, response.text
    body = response.json()
    assert body["session_years"] == []
    # And all time over nothing is today, not a run of empty months from 1970.
    all_time = await client.get("/dashboard", params={"tenant_id": TENANT, "range": "all_time"})
    assert len(all_time.json()["sessions_series"]) == 1


@pytest.mark.asyncio
async def test_dashboard_year_range_counts_only_that_year(
    client: AsyncClient, db_session: AsyncSession
):
    await _seed_across_years(db_session)

    response = await client.get(
        "/dashboard", params={"tenant_id": TENANT, "range": "year", "year": 2024}
    )

    assert response.status_code == 200, response.text
    body = response.json()
    assert body["range"]["preset"] == "year"
    assert body["range"]["start"].startswith("2024-01-01")
    assert body["range"]["end"].startswith("2025-01-01")
    assert body["kpis"]["sessions"] == 2
    # Against the whole of 2023, which held one.
    assert body["kpis"]["sessions_prior"] == 1
    assert body["range"]["granularity"] == "month"


@pytest.mark.asyncio
async def test_dashboard_year_range_needs_a_year(client: AsyncClient, db_session: AsyncSession):
    await _seed_across_years(db_session)

    response = await client.get("/dashboard", params={"tenant_id": TENANT, "range": "year"})

    assert response.status_code == 422, response.text


@pytest.mark.asyncio
async def test_dashboard_all_time_starts_at_the_first_session(
    client: AsyncClient, db_session: AsyncSession
):
    await _seed_across_years(db_session)

    response = await client.get("/dashboard", params={"tenant_id": TENANT, "range": "all_time"})

    assert response.status_code == 200, response.text
    body = response.json()
    assert body["range"]["start"].startswith("2023-06-01")
    assert body["kpis"]["sessions"] == 4
    # Nothing precedes all time, so the tile shows no comparison.
    assert body["kpis"]["sessions_prior"] == 0
    assert body["range"]["prior_start"] == body["range"]["prior_end"]


@pytest.mark.asyncio
async def test_dashboard_all_time_is_not_capped_at_three_years(
    client: AsyncClient, db_session: AsyncSession
):
    """MAX_RANGE_DAYS rejects a custom window this long; a computed one stands."""
    db_session.add(_tenant(TENANT))
    await db_session.flush()
    db_session.add(_client_row(TENANT, "cl-old", "Old Co", "OLD"))
    db_session.add(
        ProviderModel(id="prov-old", tenant_id=TENANT, display_name="C", status=BaseStatus.ACTIVE)
    )
    db_session.add(ServiceModel(id="svc-talk", tenant_id=TENANT, name="Health Talk"))
    await db_session.flush()
    db_session.add(_session(TENANT, "cl-old", "prov-old", at=datetime(2016, 1, 5, 10, tzinfo=UTC)))
    await db_session.commit()

    response = await client.get("/dashboard", params={"tenant_id": TENANT, "range": "all_time"})

    assert response.status_code == 200, response.text
    assert response.json()["range"]["start"].startswith("2016-01-05")


@pytest.mark.asyncio
async def test_dashboard_value_upcoming_risk_and_contracts(
    client: AsyncClient, db_session: AsyncSession
):
    """The blocks added for the operator's morning read.

    Delivered value sums only the priced sessions and says how many were not
    priced. Upcoming counts open future bookings into a seven-day, zero-filled
    strip. Contracts ending inside the horizon are counted; one safely past it
    is not. The risk block counts an open incident and ignores a closed one.
    """
    await _seed(db_session)
    today = utc_now().date()
    db_session.add_all(
        [
            _session(
                TENANT, "cl-dash-a", "prov-dash-1", days_ago=-2, status=SessionStatus.SCHEDULED
            ),
            _session(
                TENANT, "cl-dash-a", "prov-dash-1", days_ago=-2, status=SessionStatus.RESCHEDULED
            ),
            _session(
                TENANT, "cl-dash-a", "prov-dash-1", days_ago=-30, status=SessionStatus.SCHEDULED
            ),
            ContractModel(
                id="ct-dash-soon",
                tenant_id=TENANT,
                client_id="cl-dash-a",
                start_date=today - timedelta(days=300),
                end_date=today + timedelta(days=30),
                billing_rate={},
                payment_frequency=PaymentFrequency.MONTHLY,
                payment_status=PaymentStatus.PAID,
                status=ContractStatus.ACTIVE,
            ),
            ContractModel(
                id="ct-dash-late",
                tenant_id=TENANT,
                client_id="cl-dash-a",
                start_date=today - timedelta(days=1),
                end_date=today + timedelta(days=200),
                billing_rate={},
                payment_frequency=PaymentFrequency.MONTHLY,
                payment_status=PaymentStatus.PAID,
                status=ContractStatus.ACTIVE,
            ),
            CriticalIncidentModel(
                tenant_id=TENANT,
                client_id="cl-dash-a",
                event_description="Open incident",
                severity=CriticalIncidentSeverity.HIGH,
                affected_population_size=10,
                occurred_at=utc_now(),
                logged_by="user-dash",
                status=CriticalIncidentStatus.OPEN,
            ),
            CriticalIncidentModel(
                tenant_id=TENANT,
                client_id="cl-dash-a",
                event_description="Closed incident",
                severity=CriticalIncidentSeverity.LOW,
                affected_population_size=1,
                occurred_at=utc_now(),
                logged_by="user-dash",
                status=CriticalIncidentStatus.CLOSED,
            ),
        ]
    )
    await db_session.commit()

    response = await client.get("/dashboard", params={"tenant_id": TENANT, "range": "last_90d"})
    assert response.status_code == 200, response.text
    body = response.json()

    # Three in-range sessions priced at 100k; the fourth carries no rate.
    assert body["kpis"]["value_delivered_ugx"] == 300_000
    assert body["kpis"]["sessions_unpriced"] == 1
    assert body["kpis"]["contracts_ending_soon"] == 1

    upcoming = body["upcoming"]
    assert upcoming["total"] == 2
    assert len(upcoming["days"]) == 7
    assert sum(d["total"] for d in upcoming["days"]) == 2

    assert body["risk"] == {"crisis_flags_open": 0, "incidents_open": 1, "cases_open": 0}


@pytest.mark.asyncio
async def test_dashboard_outcome_mix_fails_closed_without_the_clinical_scope(
    client: AsyncClient, db_session: AsyncSession
):
    """The default test token carries no scopes, so the mix must be null.

    The counts are aggregate, but outcomes belong to the clinical record;
    the wall fails closed rather than arguing about aggregation. The admitted
    path is covered in test_clinical_scope_wall.py against real minting.
    """
    await _seed(db_session)

    response = await client.get("/dashboard", params={"tenant_id": TENANT, "range": "last_90d"})

    assert response.status_code == 200
    assert response.json()["outcome_mix"] is None
