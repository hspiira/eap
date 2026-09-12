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

The actual queries live in ``DashboardQueryRunner`` (infrastructure): this
route only does window math and response shaping, so it never imports an ORM
model directly.
"""

from datetime import UTC, date, datetime, timedelta

from fastapi import APIRouter, Depends, Query

from app.api.dependencies import get_dashboard_query_runner
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
from app.core.security import TokenData
from app.domain.enums import SessionType
from app.domain.enums.provider_network import ImportRowOutcome
from app.domain.exceptions import ValidationException
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

#: Every outcome that leaves a staged row unwritten and awaiting a person.
#:
#: Conflicting and Rejected belong here as much as the unresolved identities:
#: a row with no date, or one naming an organisation the practitioner did not
#: hold that day, is just as stuck. Leaving them out let a batch stuck
#: entirely on those report nothing blocked. Failed is deliberately absent,
#: being an apply-time write refusal rather than something staging held.
HELD_OUTCOMES = (
    ImportRowOutcome.MISSING_PRACTITIONER,
    ImportRowOutcome.UNMAPPED_PRACTITIONER,
    ImportRowOutcome.AMBIGUOUS_PRACTITIONER,
    ImportRowOutcome.UNRESOLVED_CLIENT,
    ImportRowOutcome.UNRESOLVED_MEMBER,
    ImportRowOutcome.UNRESOLVED_SERVICE,
    ImportRowOutcome.CONFLICTING,
    ImportRowOutcome.REJECTED,
)


class ResolvedRange:
    """The window a request asks for, with its comparison window and bucket size.

    The comparison defaults to the stretch of equal length immediately before
    the window. A year preset passes its own instead: a year is read against
    the same dates a year earlier, not against the months that happen to
    precede it.
    """

    def __init__(
        self,
        preset: RangePreset,
        start: datetime,
        end: datetime,
        prior_start: datetime | None = None,
        prior_end: datetime | None = None,
    ):
        self.preset = preset
        self.start = start
        self.end = end
        self.prior_start = prior_start if prior_start is not None else start - (end - start)
        self.prior_end = prior_end if prior_end is not None else start
        self.granularity: Granularity = _granularity_for(end - start)

    def to_info(self) -> RangeInfo:
        return RangeInfo(
            preset=self.preset,
            start=self.start.isoformat(),
            end=self.end.isoformat(),
            prior_start=self.prior_start.isoformat(),
            prior_end=self.prior_end.isoformat(),
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


def _a_year_earlier(moment: datetime) -> datetime:
    """The same calendar moment in the previous year.

    Shifted by the calendar rather than by 365 days: a leap year is 366 days
    long, so subtracting its duration from 1 January lands on 2 January and
    the comparison window silently gains a day. 29 February has no counterpart
    and falls back to the 28th.
    """
    try:
        return moment.replace(year=moment.year - 1)
    except ValueError:
        return moment.replace(year=moment.year - 1, day=28)


def _year_range(preset: RangePreset, year: int, now: datetime) -> ResolvedRange:
    """One calendar year, against the same stretch of the year before.

    The current year stops at now rather than running to 31 December, so a
    part-finished year is compared with the same part of the year before it
    and not against twelve months it has not reached yet.
    """
    if year > now.year:
        raise ValidationException("year cannot be in the future")
    start = _midnight(now).replace(year=year, month=1, day=1)
    end = now if year == now.year else start.replace(year=year + 1)
    return ResolvedRange(preset, start, end, _a_year_earlier(start), _a_year_earlier(end))


def _all_time_range(now: datetime, earliest: datetime | None) -> ResolvedRange:
    """Everything on record. No comparison window: there is nothing before it."""
    start = _midnight(earliest.astimezone(UTC)) if earliest else _midnight(now)
    return ResolvedRange("all_time", start, now, start, start)


def resolve_range(
    preset: RangePreset,
    start_raw: str | None,
    end_raw: str | None,
    *,
    year: int | None = None,
    earliest: datetime | None = None,
) -> ResolvedRange:
    """Turn a preset, or an explicit pair of dates, into a concrete window."""
    now = utc_now()
    if preset == "custom":
        return _custom_range(start_raw, end_raw, now)
    if preset == "all_time":
        return _all_time_range(now, earliest)
    if preset == "this_year":
        return _year_range(preset, now.year, now)
    if preset == "year":
        if year is None:
            raise ValidationException("year is required when range is year")
        return _year_range(preset, year, now)
    if preset == "this_week":
        return ResolvedRange(preset, _midnight(now) - timedelta(days=now.weekday()), now)
    if preset == "this_month":
        return ResolvedRange(preset, _midnight(now).replace(day=1), now)
    days = {"last_30d": 30, "last_90d": 90, "last_180d": 180}[preset]
    return ResolvedRange(preset, now - timedelta(days=days), now)


def _session_years(earliest: datetime | None) -> list[int]:
    """Years the picker may offer, newest first. Empty when nothing is delivered.

    Derived from the first delivery rather than listed by hand, so the picker
    never offers a year with nothing behind it. A year in between with no
    sessions still appears; the gap is the answer, and hiding it would read
    as though the year never existed.
    """
    if earliest is None:
        return []
    return list(range(utc_now().year, earliest.astimezone(UTC).year - 1, -1))


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


async def _sessions_series(runner, tenant_id: str, window: ResolvedRange) -> list[SeriesPoint]:
    granularity = window.granularity
    rows = await runner.sessions_series(tenant_id, window.start, window.end, granularity)

    points: dict[str, SeriesPoint] = {}
    cursor = _bucket_start(window.start, granularity)
    last = _bucket_start(window.end - timedelta(microseconds=1), granularity)
    while cursor <= last:
        points[_bucket_key(cursor, granularity)] = _empty_point(cursor, granularity)
        cursor = _next_bucket(cursor, granularity)

    for bucket_date, session_type, total in rows:
        key = _bucket_key(bucket_date, granularity)
        point = points.get(key)
        if point is not None:
            _apply_split(point, session_type, total)
    return list(points.values())


async def _category_split(runner, tenant_id: str, window: ResolvedRange) -> list[CategoryCount]:
    rows = await runner.category_split(tenant_id, window.start, window.end)
    return [CategoryCount(category=category, total=total) for category, total in rows]


async def _top_clients(runner, tenant_id: str, window: ResolvedRange) -> list[ClientSessions]:
    rows = await runner.top_clients(tenant_id, window.start, window.end, TOP_CLIENTS_LIMIT)
    return [
        ClientSessions(client_id=client_id, client_name=name, total=total)
        for client_id, name, total in rows
    ]


def _change_pct(total: int, prior: int) -> float | None:
    if prior <= 0:
        return None
    return round(((total - prior) / prior) * 100, 1)


async def _trending_services(runner, tenant_id: str, window: ResolvedRange) -> list[ServiceTrend]:
    """Demand per service inside the range, measured against the prior window."""
    current = await runner.service_counts(tenant_id, window.start, window.end)
    prior = await runner.service_counts(tenant_id, window.prior_start, window.start)
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
    runner, tenant_id: str
) -> tuple[ImportBatchSummary | None, list[ImportQueueEntry], int]:
    batch = await runner.latest_import_batch(tenant_id)
    if batch is None:
        return None, [], 0

    by_outcome = await runner.import_row_outcomes(batch.id)
    queues = sorted(
        (
            ImportQueueEntry(outcome=outcome.value, total=by_outcome[outcome])
            for outcome in HELD_OUTCOMES
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
        failed=by_outcome.get(ImportRowOutcome.FAILED, 0),
        applied_at=batch.applied_at.isoformat() if batch.applied_at else None,
    )
    return summary, queues, blocked


async def _data_quality(
    runner, tenant_id: str, clients_total: int, clients_with_roster: int
) -> DataQuality:
    missing_outcome, missing_rate, providers_pending = await runner.data_quality_counts(tenant_id)
    return DataQuality(
        sessions_missing_outcome=missing_outcome,
        sessions_missing_rate=missing_rate,
        clients_without_roster=max(clients_total - clients_with_roster, 0),
        providers_pending=providers_pending,
        sessions_awaiting_confirmation=await runner.sessions_awaiting_confirmation(tenant_id),
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
    year: int | None = Query(
        None, ge=1970, le=2999, description="Calendar year when range is year"
    ),
    _current_user: TokenData = Depends(require_same_tenant),
    runner=Depends(get_dashboard_query_runner),
) -> DashboardResponse:
    """All dashboard figures in one read, computed against the same instant."""
    earliest = await runner.earliest_session(tenant_id)
    window = resolve_range(range_preset, start, end, year=year, earliest=earliest)

    sessions, sessions_prior, clients_served = await runner.session_kpis(
        tenant_id, window.start, window.end, window.prior_start, window.prior_end
    )
    covered, with_roster, clients_total = await runner.coverage(tenant_id)
    import_batch, import_queues, backlog = await _import_state(runner, tenant_id)

    return DashboardResponse(
        range=window.to_info(),
        session_years=_session_years(earliest),
        kpis=DashboardKpis(
            sessions=sessions,
            sessions_prior=sessions_prior,
            clients_served=clients_served,
            covered_members=covered,
            clients_with_roster=with_roster,
            clients_total=clients_total,
            import_backlog=backlog,
        ),
        sessions_series=await _sessions_series(runner, tenant_id, window),
        sessions_by_category=await _category_split(runner, tenant_id, window),
        top_clients=await _top_clients(runner, tenant_id, window),
        trending_services=await _trending_services(runner, tenant_id, window),
        import_queues=import_queues,
        import_batch=import_batch,
        data_quality=await _data_quality(runner, tenant_id, clients_total, with_roster),
    )
