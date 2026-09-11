"""Dashboard API contracts.

One aggregate, tenant-scoped read model for the home page. Every figure is a
count or a small grouped series; no record-level data leaves this endpoint,
so it discloses nothing a list endpoint would not.

Delivered work means completed sessions. Scheduled bookings are not delivery
and are deliberately absent from the series; a booking pipeline would be its
own series with its own name.

Flow figures (the series, the groupings, the trending services) are scoped to
the requested range. Stock figures (covered members, the import backlog) count
what stands today and carry no range.
"""

from typing import Literal

from pydantic import BaseModel, Field

RangePreset = Literal[
    "this_week",
    "this_month",
    "this_year",
    "year",
    "all_time",
    "last_30d",
    "last_90d",
    "last_180d",
    "custom",
]
Granularity = Literal["day", "week", "month"]


class RangeInfo(BaseModel):
    """The resolved window the flow figures describe."""

    preset: RangePreset
    start: str = Field(..., description="Inclusive window start, ISO 8601")
    end: str = Field(..., description="Exclusive window end, ISO 8601")
    prior_start: str = Field(..., description="Inclusive start of the comparison window")
    prior_end: str = Field(
        ...,
        description=(
            "Exclusive end of the comparison window. Equal to `start` for every preset that "
            "compares against the stretch immediately before it; a year preset instead "
            "compares against the same dates a year earlier, so the two windows do not touch."
        ),
    )
    granularity: Granularity = Field(
        ..., description="Bucket size of sessions_series, chosen from the window length"
    )


class DashboardKpis(BaseModel):
    """Headline counts. Session counts follow the range; the rest are stock."""

    sessions: int = Field(..., description="Completed sessions inside the range")
    sessions_prior: int = Field(
        ..., description="Completed sessions in the comparison window, for the delta"
    )
    clients_served: int = Field(
        ..., description="Distinct clients with a completed session inside the range"
    )
    covered_members: int = Field(..., description="Eligible members with Active status")
    clients_with_roster: int = Field(
        ..., description="Clients that have at least one eligible member on file"
    )
    clients_total: int = Field(..., description="Clients on the tenant, any status")
    import_backlog: int = Field(
        ...,
        description="Rows in the current import batch still blocked on an unresolved identity",
    )


class SeriesPoint(BaseModel):
    """One bucket of completed sessions, split by how it was delivered.

    `unknown` carries sessions whose source recorded no delivery type. It is
    kept as its own band rather than folded into either, so the chart never
    asserts a delivery type the record does not carry.
    """

    bucket: str = Field(..., description="Bucket start: YYYY-MM-DD, or YYYY-MM when monthly")
    label: str = Field(..., description="Display label for the bucket")
    physical: int
    online: int
    unknown: int
    total: int


class CategoryCount(BaseModel):
    """Completed sessions per session category inside the range."""

    category: str
    total: int


class ClientSessions(BaseModel):
    """Completed sessions per client inside the range."""

    client_id: str
    client_name: str
    total: int


class ServiceTrend(BaseModel):
    """One service's demand inside the range, against the prior window."""

    service_id: str
    service_name: str
    total: int
    prior_total: int
    change_pct: float | None = Field(
        None, description="Percentage change against the prior window; null when it had no sessions"
    )


class ImportQueueEntry(BaseModel):
    """One unresolved outcome bucket in the current import batch."""

    outcome: str
    total: int


class ImportBatchSummary(BaseModel):
    """The batch the backlog figures describe, as a part-to-whole composition."""

    file_name: str
    status: str
    row_count: int
    accepted: int
    duplicate: int
    blocked: int = Field(..., description="Rows held on an unresolved identity")
    applied_at: str | None = None


class DataQuality(BaseModel):
    """Derived gaps that block reporting, each one an actionable queue."""

    sessions_missing_outcome: int = Field(
        ..., description="Completed sessions with no clinical outcome recorded"
    )
    sessions_missing_rate: int = Field(..., description="Completed sessions with no rate")
    clients_without_roster: int = Field(..., description="Clients with no eligible members on file")
    providers_pending: int = Field(..., description="Practitioners not yet activated")


class DashboardResponse(BaseModel):
    """The whole dashboard in one authenticated, tenant-scoped read."""

    range: RangeInfo
    session_years: list[int] = Field(
        default_factory=list,
        description=(
            "Years that actually have a completed session, newest first. What the year "
            "picker offers, so it never lists a year with nothing behind it. Empty for a "
            "tenant that has delivered nothing."
        ),
    )
    kpis: DashboardKpis
    sessions_series: list[SeriesPoint]
    sessions_by_category: list[CategoryCount]
    top_clients: list[ClientSessions]
    trending_services: list[ServiceTrend]
    import_queues: list[ImportQueueEntry]
    import_batch: ImportBatchSummary | None = Field(
        None, description="Absent when the tenant has never staged an import"
    )
    data_quality: DataQuality
