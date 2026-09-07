"""Dashboard aggregate endpoint.

Seeds a small tenant directly through the models and checks every block of
the response: KPI counts, the zero-filled monthly series, the category and
client groupings, the import backlog scoped to the latest non-abandoned
batch, and the derived data-quality queues. A second tenant's data proves
the scoping.
"""

from datetime import timedelta

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
)
from app.domain.enums.provider_network import ImportBatchStatus, ImportRowOutcome
from app.infrastructure.models.client_model import ClientModel
from app.infrastructure.models.eligible_member_model import EligibleMemberModel
from app.infrastructure.models.provider_model import ProviderModel
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
    days_ago: int,
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
        service_id="svc-1",
        provider_id=provider_id,
        client_id=client_id,
        scheduled_at=now - timedelta(days=days_ago),
        status=status,
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
    await db.flush()

    db.add_all(
        [
            # Recent window: three completed for Alpha, one for Beta.
            _session(TENANT, "cl-dash-a", provider, days_ago=5),
            _session(TENANT, "cl-dash-a", provider, days_ago=10, category=SessionCategory.FAMILY),
            _session(
                TENANT,
                "cl-dash-a",
                provider,
                days_ago=20,
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

    response = await client.get("/dashboard", params={"tenant_id": TENANT})
    assert response.status_code == 200
    body = response.json()

    kpis = body["kpis"]
    assert kpis["sessions_90d"] == 4
    assert kpis["sessions_prior_90d"] == 1
    assert kpis["clients_served_90d"] == 2
    assert kpis["covered_members"] == 2
    assert kpis["clients_with_roster"] == 1
    assert kpis["clients_total"] == 2
    assert kpis["import_backlog"] == 3

    months = body["sessions_monthly"]
    assert len(months) == 12
    assert sum(m["total"] for m in months) == 5
    assert months[-1]["month"] == utc_now().strftime("%Y-%m")

    categories = {c["category"]: c["total"] for c in body["sessions_by_category"]}
    assert categories == {"Group": 4, "Family": 1}

    top = [(c["client_name"], c["total"]) for c in body["top_clients"]]
    assert top == [("Alpha Bank", 4), ("Beta Ltd", 1)]

    queues = [(q["outcome"], q["total"]) for q in body["import_queues"]]
    assert queues == [("UnresolvedMember", 2), ("MissingPractitioner", 1)]
    assert body["import_batch"]["file_name"] == "sessions.csv"
    assert body["import_batch"]["status"] == "Applied"
    assert body["import_batch"]["accepted"] == 1

    quality = body["data_quality"]
    assert quality["sessions_missing_outcome"] == 1
    assert quality["sessions_missing_rate"] == 1
    assert quality["clients_without_roster"] == 1
    assert quality["providers_pending"] == 1


@pytest.mark.asyncio
async def test_dashboard_empty_tenant(client: AsyncClient, db_session: AsyncSession):
    db_session.add(_tenant(TENANT))
    await db_session.commit()

    response = await client.get("/dashboard", params={"tenant_id": TENANT})
    assert response.status_code == 200
    body = response.json()
    assert body["kpis"]["clients_total"] == 0
    assert body["kpis"]["import_backlog"] == 0
    assert body["import_batch"] is None
    assert body["import_queues"] == []
    assert len(body["sessions_monthly"]) == 12
    assert all(m["total"] == 0 for m in body["sessions_monthly"])
