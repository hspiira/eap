"""Dashboard aggregate API.

One authenticated, tenant-scoped read that replaces the frontend's fan-out of
limit=1 list calls. Every figure is computed here with grouped counts, so the
page loads in one request and the numbers all describe the same instant.

Sessions count as delivered only when their status is Completed and they are
not soft-deleted. The import backlog describes the most recent batch that was
not abandoned: an abandoned batch's rows are dead, while a staged or applied
batch's unresolved rows are the queue that better reference data would unlock.
"""

from datetime import datetime, timedelta

from fastapi import APIRouter, Depends, Query
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.schemas.dashboard_schemas import (
    CategoryCount,
    ClientSessions,
    DashboardKpis,
    DashboardResponse,
    DataQuality,
    ImportBatchSummary,
    ImportQueueEntry,
    MonthlySessions,
)
from app.core.authorization import require_same_tenant
from app.core.database import get_db
from app.core.security import TokenData
from app.domain.enums import BaseStatus, EligibilityStatus, SessionStatus
from app.domain.enums.provider_network import ImportBatchStatus, ImportRowOutcome
from app.infrastructure.models.client_model import ClientModel
from app.infrastructure.models.eligible_member_model import EligibleMemberModel
from app.infrastructure.models.provider_model import ProviderModel
from app.infrastructure.models.service_session_model import ServiceSessionModel
from app.infrastructure.models.session_import_model import (
    SessionImportBatchModel,
    SessionImportRowModel,
)
from app.shared.decorators import readonly
from app.shared.utils.datetime import utc_now

router = APIRouter(prefix="/dashboard", tags=["dashboard"])

TREND_MONTHS = 12
TOP_CLIENTS_LIMIT = 8

UNRESOLVED_OUTCOMES = (
    ImportRowOutcome.MISSING_PRACTITIONER,
    ImportRowOutcome.UNMAPPED_PRACTITIONER,
    ImportRowOutcome.AMBIGUOUS_PRACTITIONER,
    ImportRowOutcome.UNRESOLVED_CLIENT,
    ImportRowOutcome.UNRESOLVED_MEMBER,
    ImportRowOutcome.UNRESOLVED_SERVICE,
)


def _month_floor(moment: datetime) -> datetime:
    return moment.replace(day=1, hour=0, minute=0, second=0, microsecond=0)


def _months_back(moment: datetime, months: int) -> datetime:
    """The first instant of the month `months` before the given moment's month."""
    index = moment.year * 12 + (moment.month - 1) - months
    return _month_floor(moment).replace(year=index // 12, month=index % 12 + 1)


def _completed_sessions(tenant_id: str):
    return (
        ServiceSessionModel.tenant_id == tenant_id,
        ServiceSessionModel.deleted_at.is_(None),
        ServiceSessionModel.status == SessionStatus.COMPLETED,
    )


async def _count(db: AsyncSession, stmt) -> int:
    return int((await db.execute(stmt)).scalar_one() or 0)


async def _session_kpis(db: AsyncSession, tenant_id: str, now: datetime) -> tuple[int, int, int]:
    window_start = now - timedelta(days=90)
    prior_start = now - timedelta(days=180)
    recent = await _count(
        db,
        select(func.count(ServiceSessionModel.id)).where(
            *_completed_sessions(tenant_id), ServiceSessionModel.scheduled_at >= window_start
        ),
    )
    prior = await _count(
        db,
        select(func.count(ServiceSessionModel.id)).where(
            *_completed_sessions(tenant_id),
            ServiceSessionModel.scheduled_at >= prior_start,
            ServiceSessionModel.scheduled_at < window_start,
        ),
    )
    clients_served = await _count(
        db,
        select(func.count(func.distinct(ServiceSessionModel.client_id))).where(
            *_completed_sessions(tenant_id), ServiceSessionModel.scheduled_at >= window_start
        ),
    )
    return recent, prior, clients_served


async def _coverage(db: AsyncSession, tenant_id: str) -> tuple[int, int, int]:
    covered = await _count(
        db,
        select(func.count(EligibleMemberModel.id)).where(
            EligibleMemberModel.tenant_id == tenant_id,
            EligibleMemberModel.status == EligibilityStatus.ACTIVE,
        ),
    )
    with_roster = await _count(
        db,
        select(func.count(func.distinct(EligibleMemberModel.client_id))).where(
            EligibleMemberModel.tenant_id == tenant_id
        ),
    )
    clients_total = await _count(
        db,
        select(func.count(ClientModel.id)).where(
            ClientModel.tenant_id == tenant_id, ClientModel.deleted_at.is_(None)
        ),
    )
    return covered, with_roster, clients_total


async def _monthly_series(
    db: AsyncSession, tenant_id: str, window_start: datetime, now: datetime
) -> list[MonthlySessions]:
    # Normalize to a naive UTC timestamp first: date_trunc on a timestamptz
    # buckets by the connection's timezone, which shifts boundary sessions
    # into the wrong month depending on server configuration.
    month = func.date_trunc("month", func.timezone("UTC", ServiceSessionModel.scheduled_at))
    rows = await db.execute(
        select(month, func.count(ServiceSessionModel.id))
        .where(
            *_completed_sessions(tenant_id),
            ServiceSessionModel.scheduled_at >= window_start,
        )
        .group_by(month)
    )
    counts = {row[0].strftime("%Y-%m"): int(row[1]) for row in rows}
    series = []
    for offset in range(TREND_MONTHS - 1, -1, -1):
        key = _months_back(now, offset).strftime("%Y-%m")
        series.append(MonthlySessions(month=key, total=counts.get(key, 0)))
    return series


async def _category_split(
    db: AsyncSession, tenant_id: str, window_start: datetime
) -> list[CategoryCount]:
    rows = await db.execute(
        select(ServiceSessionModel.category, func.count(ServiceSessionModel.id))
        .where(
            *_completed_sessions(tenant_id),
            ServiceSessionModel.scheduled_at >= window_start,
            ServiceSessionModel.category.is_not(None),
        )
        .group_by(ServiceSessionModel.category)
        .order_by(func.count(ServiceSessionModel.id).desc())
    )
    return [CategoryCount(category=category.value, total=int(total)) for category, total in rows]


async def _top_clients(
    db: AsyncSession, tenant_id: str, window_start: datetime
) -> list[ClientSessions]:
    rows = await db.execute(
        select(ClientModel.id, ClientModel.name, func.count(ServiceSessionModel.id))
        .join(ClientModel, ClientModel.id == ServiceSessionModel.client_id)
        .where(
            *_completed_sessions(tenant_id),
            ServiceSessionModel.scheduled_at >= window_start,
        )
        .group_by(ClientModel.id, ClientModel.name)
        .order_by(func.count(ServiceSessionModel.id).desc())
        .limit(TOP_CLIENTS_LIMIT)
    )
    return [
        ClientSessions(client_id=client_id, client_name=name, total=int(total))
        for client_id, name, total in rows
    ]


async def _import_state(
    db: AsyncSession, tenant_id: str
) -> tuple[ImportBatchSummary | None, list[ImportQueueEntry], int]:
    batch = (
        await db.execute(
            select(SessionImportBatchModel)
            .where(
                SessionImportBatchModel.tenant_id == tenant_id,
                SessionImportBatchModel.status != ImportBatchStatus.ABANDONED,
            )
            .order_by(SessionImportBatchModel.created_at.desc())
            .limit(1)
        )
    ).scalar_one_or_none()
    if batch is None:
        return None, [], 0

    rows = await db.execute(
        select(SessionImportRowModel.outcome, func.count(SessionImportRowModel.id))
        .where(SessionImportRowModel.batch_id == batch.id)
        .group_by(SessionImportRowModel.outcome)
    )
    by_outcome = {outcome: int(total) for outcome, total in rows}
    queues = sorted(
        (
            ImportQueueEntry(outcome=outcome.value, total=by_outcome[outcome])
            for outcome in UNRESOLVED_OUTCOMES
            if by_outcome.get(outcome)
        ),
        key=lambda entry: entry.total,
        reverse=True,
    )
    summary = ImportBatchSummary(
        file_name=batch.file_name,
        status=batch.status.value,
        row_count=batch.row_count,
        accepted=by_outcome.get(ImportRowOutcome.ACCEPTED, 0),
        applied_at=batch.applied_at.isoformat() if batch.applied_at else None,
    )
    return summary, queues, sum(entry.total for entry in queues)


async def _data_quality(
    db: AsyncSession, tenant_id: str, clients_total: int, clients_with_roster: int
) -> DataQuality:
    missing_outcome = await _count(
        db,
        select(func.count(ServiceSessionModel.id)).where(
            *_completed_sessions(tenant_id), ServiceSessionModel.clinical_outcome.is_(None)
        ),
    )
    missing_rate = await _count(
        db,
        select(func.count(ServiceSessionModel.id)).where(
            *_completed_sessions(tenant_id), ServiceSessionModel.rate_ugx.is_(None)
        ),
    )
    providers_pending = await _count(
        db,
        select(func.count(ProviderModel.id)).where(
            ProviderModel.tenant_id == tenant_id,
            ProviderModel.deleted_at.is_(None),
            ProviderModel.status == BaseStatus.PENDING,
        ),
    )
    return DataQuality(
        sessions_missing_outcome=missing_outcome,
        sessions_missing_rate=missing_rate,
        clients_without_roster=max(clients_total - clients_with_roster, 0),
        providers_pending=providers_pending,
    )


@router.get(
    "",
    response_model=DashboardResponse,
    summary="Aggregate dashboard figures for the caller's tenant",
)
@readonly()
async def get_dashboard(
    tenant_id: str = Query(..., description="Tenant identifier"),
    _current_user: TokenData = Depends(require_same_tenant),
    db: AsyncSession = Depends(get_db),
) -> DashboardResponse:
    """All dashboard figures in one read, computed against the same instant."""
    now = utc_now()
    window_start = _months_back(now, TREND_MONTHS - 1)

    sessions_90d, sessions_prior_90d, clients_served = await _session_kpis(db, tenant_id, now)
    covered, with_roster, clients_total = await _coverage(db, tenant_id)
    import_batch, import_queues, backlog = await _import_state(db, tenant_id)

    return DashboardResponse(
        kpis=DashboardKpis(
            sessions_90d=sessions_90d,
            sessions_prior_90d=sessions_prior_90d,
            clients_served_90d=clients_served,
            covered_members=covered,
            clients_with_roster=with_roster,
            clients_total=clients_total,
            import_backlog=backlog,
        ),
        sessions_monthly=await _monthly_series(db, tenant_id, window_start, now),
        sessions_by_category=await _category_split(db, tenant_id, window_start),
        top_clients=await _top_clients(db, tenant_id, window_start),
        import_queues=import_queues,
        import_batch=import_batch,
        data_quality=await _data_quality(db, tenant_id, clients_total, with_roster),
    )
