"""Dashboard aggregate API.

One authenticated, tenant-scoped read that replaces the frontend's fan-out of
limit=1 list calls. Every figure is computed here with grouped counts, so the
page loads in one request and the numbers all describe the same instant.

Sessions count as delivered only when their status is Completed and they are
not soft-deleted. The import backlog describes the most recent batch that was
not abandoned: an abandoned batch's rows are dead, while a staged or applied
batch's unresolved rows are the queue that better reference data would unlock.

Flow figures follow the requested range; the caller picks a preset or supplies
its own dates. Bucket size is derived from the window rather than requested,
so a year cannot be asked for one bucket per day.
"""

from datetime import UTC, date, datetime, timedelta

from fastapi import APIRouter, Depends, Query
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.schemas.dashboard_schemas import (
    CategoryCount,
    ClientSessions,
    DashboardKpis,
    DashboardResponse,
    DataQuality,
    Granularity,
    ImportBatchSummary,
    ImportQueueEntry,
    RangeInfo,
    RangePreset,
    SeriesPoint,
    ServiceTrend,
)
from app.core.authorization import require_same_tenant
from app.core.database import get_db
from app.core.security import TokenData
from app.domain.enums import BaseStatus, EligibilityStatus, SessionStatus, SessionType
from app.domain.enums.provider_network import ImportBatchStatus, ImportRowOutcome
from app.domain.exceptions import ValidationException
from app.infrastructure.models.client_model import ClientModel
from app.infrastructure.models.eligible_member_model import EligibleMemberModel
from app.infrastructure.models.provider_model import ProviderModel
from app.infrastructure.models.service_model import ServiceModel
from app.infrastructure.models.service_session_model import ServiceSessionModel
from app.infrastructure.models.session_import_model import (
    SessionImportBatchModel,
    SessionImportRowModel,
)
from app.shared.decorators import readonly
from app.shared.utils.datetime import utc_now

router = APIRouter(prefix="/dashboard", tags=["dashboard"])

TOP_CLIENTS_LIMIT = 5
TRENDING_SERVICES_LIMIT = 6
MAX_RANGE_DAYS = 1095

DAILY_MAX_DAYS = 31
WEEKLY_MAX_DAYS = 120

MONTH_NAMES = (
    "Jan",
    "Feb",
    "Mar",
    "Apr",
    "May",
    "Jun",
    "Jul",
    "Aug",
    "Sep",
    "Oct",
    "Nov",
    "Dec",
)

UNRESOLVED_OUTCOMES = (
    ImportRowOutcome.MISSING_PRACTITIONER,
    ImportRowOutcome.UNMAPPED_PRACTITIONER,
    ImportRowOutcome.AMBIGUOUS_PRACTITIONER,
    ImportRowOutcome.UNRESOLVED_CLIENT,
    ImportRowOutcome.UNRESOLVED_MEMBER,
    ImportRowOutcome.UNRESOLVED_SERVICE,
)


class ResolvedRange:
    """The window a request asks for, with its prior window and bucket size."""

    def __init__(self, preset: RangePreset, start: datetime, end: datetime):
        self.preset = preset
        self.start = start
        self.end = end
        self.prior_start = start - (end - start)
        self.granularity: Granularity = _granularity_for(end - start)

    def to_info(self) -> RangeInfo:
        return RangeInfo(
            preset=self.preset,
            start=self.start.isoformat(),
            end=self.end.isoformat(),
            prior_start=self.prior_start.isoformat(),
            granularity=self.granularity,
        )


def _granularity_for(span: timedelta) -> Granularity:
    if span.days <= DAILY_MAX_DAYS:
        return "day"
    if span.days <= WEEKLY_MAX_DAYS:
        return "week"
    return "month"


def _midnight(moment: datetime) -> datetime:
    return moment.replace(hour=0, minute=0, second=0, microsecond=0)


def _parse_boundary(raw: str, field: str) -> datetime:
    """A calendar date or full timestamp, always read as UTC."""
    try:
        parsed = datetime.fromisoformat(raw)
    except ValueError:
        raise ValidationException(f"{field} must be an ISO 8601 date or timestamp") from None
    if parsed.tzinfo is None:
        return parsed.replace(tzinfo=UTC)
    return parsed.astimezone(UTC)


def _custom_range(start_raw: str | None, end_raw: str | None, now: datetime) -> ResolvedRange:
    if not start_raw:
        raise ValidationException("start is required when range is custom")
    start = _midnight(_parse_boundary(start_raw, "start"))
    end = _parse_boundary(end_raw, "end") if end_raw else now
    if end <= start:
        raise ValidationException("end must be after start")
    if (end - start).days > MAX_RANGE_DAYS:
        raise ValidationException(f"range must not exceed {MAX_RANGE_DAYS} days")
    return ResolvedRange("custom", start, end)


def resolve_range(preset: RangePreset, start_raw: str | None, end_raw: str | None) -> ResolvedRange:
    """Turn a preset, or an explicit pair of dates, into a concrete window."""
    now = utc_now()
    if preset == "custom":
        return _custom_range(start_raw, end_raw, now)
    if preset == "this_week":
        return ResolvedRange(preset, _midnight(now) - timedelta(days=now.weekday()), now)
    if preset == "this_month":
        return ResolvedRange(preset, _midnight(now).replace(day=1), now)
    days = {"last_30d": 30, "last_90d": 90, "last_180d": 180}[preset]
    return ResolvedRange(preset, now - timedelta(days=days), now)


def _completed_sessions(tenant_id: str):
    return (
        ServiceSessionModel.tenant_id == tenant_id,
        ServiceSessionModel.deleted_at.is_(None),
        ServiceSessionModel.status == SessionStatus.COMPLETED,
    )


def _within(start: datetime, end: datetime):
    return (
        ServiceSessionModel.scheduled_at >= start,
        ServiceSessionModel.scheduled_at < end,
    )


def _utc_scheduled_at():
    """Normalize before truncating.

    date_trunc on a timestamptz buckets by the connection's timezone, which
    moves a boundary session into the wrong bucket depending on server
    configuration.
    """
    return func.timezone("UTC", ServiceSessionModel.scheduled_at)


async def _count(db: AsyncSession, stmt) -> int:
    return int((await db.execute(stmt)).scalar_one() or 0)


async def _session_kpis(
    db: AsyncSession, tenant_id: str, window: ResolvedRange
) -> tuple[int, int, int]:
    current = await _count(
        db,
        select(func.count(ServiceSessionModel.id)).where(
            *_completed_sessions(tenant_id), *_within(window.start, window.end)
        ),
    )
    prior = await _count(
        db,
        select(func.count(ServiceSessionModel.id)).where(
            *_completed_sessions(tenant_id), *_within(window.prior_start, window.start)
        ),
    )
    clients_served = await _count(
        db,
        select(func.count(func.distinct(ServiceSessionModel.client_id))).where(
            *_completed_sessions(tenant_id), *_within(window.start, window.end)
        ),
    )
    return current, prior, clients_served


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


def _bucket_start(moment: datetime, granularity: Granularity) -> date:
    day = moment.astimezone(UTC).date()
    if granularity == "day":
        return day
    if granularity == "week":
        return day - timedelta(days=day.weekday())
    return day.replace(day=1)


def _next_bucket(current: date, granularity: Granularity) -> date:
    if granularity == "day":
        return current + timedelta(days=1)
    if granularity == "week":
        return current + timedelta(days=7)
    index = current.year * 12 + current.month
    return date(index // 12, index % 12 + 1, 1)


def _bucket_key(bucket: date, granularity: Granularity) -> str:
    return bucket.strftime("%Y-%m") if granularity == "month" else bucket.isoformat()


def _bucket_label(bucket: date, granularity: Granularity) -> str:
    month = MONTH_NAMES[bucket.month - 1]
    if granularity == "month":
        return f"{month} {bucket.year}"
    if granularity == "week":
        return f"{bucket.day} {month}"
    return f"{bucket.day} {month}"


def _empty_point(bucket: date, granularity: Granularity) -> SeriesPoint:
    return SeriesPoint(
        bucket=_bucket_key(bucket, granularity),
        label=_bucket_label(bucket, granularity),
        physical=0,
        online=0,
        unknown=0,
        total=0,
    )


def _apply_split(point: SeriesPoint, session_type: SessionType | None, total: int) -> None:
    if session_type == SessionType.PHYSICAL:
        point.physical += total
    elif session_type == SessionType.ONLINE:
        point.online += total
    else:
        point.unknown += total
    point.total += total


async def _sessions_series(
    db: AsyncSession, tenant_id: str, window: ResolvedRange
) -> list[SeriesPoint]:
    granularity = window.granularity
    bucket = func.date_trunc(granularity, _utc_scheduled_at())
    rows = await db.execute(
        select(bucket, ServiceSessionModel.session_type, func.count(ServiceSessionModel.id))
        .where(*_completed_sessions(tenant_id), *_within(window.start, window.end))
        .group_by(bucket, ServiceSessionModel.session_type)
    )

    points: dict[str, SeriesPoint] = {}
    cursor = _bucket_start(window.start, granularity)
    last = _bucket_start(window.end - timedelta(microseconds=1), granularity)
    while cursor <= last:
        points[_bucket_key(cursor, granularity)] = _empty_point(cursor, granularity)
        cursor = _next_bucket(cursor, granularity)

    for bucket_at, session_type, total in rows:
        key = _bucket_key(bucket_at.date(), granularity)
        point = points.get(key)
        if point is not None:
            _apply_split(point, session_type, int(total))
    return list(points.values())


async def _category_split(
    db: AsyncSession, tenant_id: str, window: ResolvedRange
) -> list[CategoryCount]:
    rows = await db.execute(
        select(ServiceSessionModel.category, func.count(ServiceSessionModel.id))
        .where(
            *_completed_sessions(tenant_id),
            *_within(window.start, window.end),
            ServiceSessionModel.category.is_not(None),
        )
        .group_by(ServiceSessionModel.category)
        .order_by(func.count(ServiceSessionModel.id).desc())
    )
    return [CategoryCount(category=category.value, total=int(total)) for category, total in rows]


async def _top_clients(
    db: AsyncSession, tenant_id: str, window: ResolvedRange
) -> list[ClientSessions]:
    rows = await db.execute(
        select(ClientModel.id, ClientModel.name, func.count(ServiceSessionModel.id))
        .join(ClientModel, ClientModel.id == ServiceSessionModel.client_id)
        .where(*_completed_sessions(tenant_id), *_within(window.start, window.end))
        .group_by(ClientModel.id, ClientModel.name)
        .order_by(func.count(ServiceSessionModel.id).desc())
        .limit(TOP_CLIENTS_LIMIT)
    )
    return [
        ClientSessions(client_id=client_id, client_name=name, total=int(total))
        for client_id, name, total in rows
    ]


async def _service_counts(
    db: AsyncSession, tenant_id: str, start: datetime, end: datetime
) -> dict[str, tuple[str, int]]:
    rows = await db.execute(
        select(ServiceModel.id, ServiceModel.name, func.count(ServiceSessionModel.id))
        .join(ServiceModel, ServiceModel.id == ServiceSessionModel.service_id)
        .where(*_completed_sessions(tenant_id), *_within(start, end))
        .group_by(ServiceModel.id, ServiceModel.name)
    )
    return {service_id: (name, int(total)) for service_id, name, total in rows}


def _change_pct(total: int, prior: int) -> float | None:
    if prior <= 0:
        return None
    return round(((total - prior) / prior) * 100, 1)


async def _trending_services(
    db: AsyncSession, tenant_id: str, window: ResolvedRange
) -> list[ServiceTrend]:
    """Demand per service inside the range, measured against the prior window."""
    current = await _service_counts(db, tenant_id, window.start, window.end)
    prior = await _service_counts(db, tenant_id, window.prior_start, window.start)
    trends = [
        ServiceTrend(
            service_id=service_id,
            service_name=name,
            total=total,
            prior_total=prior.get(service_id, ("", 0))[1],
            change_pct=_change_pct(total, prior.get(service_id, ("", 0))[1]),
        )
        for service_id, (name, total) in current.items()
    ]
    trends.sort(key=lambda t: t.total, reverse=True)
    return trends[:TRENDING_SERVICES_LIMIT]


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
    blocked = sum(entry.total for entry in queues)
    summary = ImportBatchSummary(
        file_name=batch.file_name,
        status=batch.status.value,
        row_count=batch.row_count,
        accepted=by_outcome.get(ImportRowOutcome.ACCEPTED, 0),
        duplicate=by_outcome.get(ImportRowOutcome.DUPLICATE, 0),
        blocked=blocked,
        applied_at=batch.applied_at.isoformat() if batch.applied_at else None,
    )
    return summary, queues, blocked


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
    range_preset: RangePreset = Query(
        "last_90d", alias="range", description="Window the flow figures cover"
    ),
    start: str | None = Query(None, description="Window start when range is custom, ISO 8601"),
    end: str | None = Query(None, description="Window end when range is custom, ISO 8601"),
    _current_user: TokenData = Depends(require_same_tenant),
    db: AsyncSession = Depends(get_db),
) -> DashboardResponse:
    """All dashboard figures in one read, computed against the same instant."""
    window = resolve_range(range_preset, start, end)

    sessions, sessions_prior, clients_served = await _session_kpis(db, tenant_id, window)
    covered, with_roster, clients_total = await _coverage(db, tenant_id)
    import_batch, import_queues, backlog = await _import_state(db, tenant_id)

    return DashboardResponse(
        range=window.to_info(),
        kpis=DashboardKpis(
            sessions=sessions,
            sessions_prior=sessions_prior,
            clients_served=clients_served,
            covered_members=covered,
            clients_with_roster=with_roster,
            clients_total=clients_total,
            import_backlog=backlog,
        ),
        sessions_series=await _sessions_series(db, tenant_id, window),
        sessions_by_category=await _category_split(db, tenant_id, window),
        top_clients=await _top_clients(db, tenant_id, window),
        trending_services=await _trending_services(db, tenant_id, window),
        import_queues=import_queues,
        import_batch=import_batch,
        data_quality=await _data_quality(db, tenant_id, clients_total, with_roster),
    )
