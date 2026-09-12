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
        description="Rows in the current import batch that staging held, for any reason",
    )
    value_delivered_ugx: int = Field(
        ...,
        description=(
            "Sum of session rates over completed sessions inside the range. Only sessions "
            "that carry a rate contribute; sessions_unpriced says how many did not."
        ),
    )
    sessions_unpriced: int = Field(
        ..., description="Completed sessions inside the range with no rate recorded"
    )
    contracts_ending_soon: int = Field(
        ..., description="Active contracts whose end date falls within the next 60 days"
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


class OutcomeCount(BaseModel):
    """Completed sessions per clinical outcome inside the range.

    `outcome` is None for sessions whose outcome was never recorded; the
    client renders that as its own "Not recorded" band rather than folding it
    into a real outcome.
    """

    outcome: str | None
    total: int


class UpcomingDay(BaseModel):
    """Bookings scheduled on one of the next seven days."""

    bucket: str = Field(..., description="Day, YYYY-MM-DD")
    label: str = Field(..., description="Display label for the day")
    total: int


class UpcomingBookings(BaseModel):
    """The booking pipeline for the week ahead.

    This reopens the earlier decision that scheduled bookings stay off the
    dashboard: they are still not delivery and never enter the sessions
    series, but they get their own card under their own name, which is what
    that decision asked of them.
    """

    total: int = Field(..., description="Open bookings in the next seven days")
    days: list[UpcomingDay]


class RiskCounts(BaseModel):
    """Open safety work. Stock figures; a crisis does not follow a range."""

    crisis_flags_open: int = Field(
        ..., description="Outreach records flagged crisis whose outreach is still open"
    )
    incidents_open: int = Field(..., description="Critical incidents not yet closed")
    cases_open: int = Field(..., description="Clinical cases currently open")


class DataQuality(BaseModel):
    """Derived gaps that block reporting, each one an actionable queue."""

    sessions_missing_outcome: int = Field(
        ..., description="Completed sessions with no clinical outcome recorded"
    )
    sessions_missing_rate: int = Field(..., description="Completed sessions with no rate")
    clients_without_roster: int = Field(..., description="Clients with no eligible members on file")
    providers_pending: int = Field(..., description="Practitioners not yet activated")
    sessions_awaiting_confirmation: int = Field(
        0,
        description=(
            "Bookings whose date has passed that nobody has confirmed or closed. "
            "Delivery happens outside the system, so these stay open until a "
            "counsellor's log accounts for them."
        ),
    )


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
    data_quality: DataQuality
    upcoming: UpcomingBookings
    risk: RiskCounts
    outcome_mix: list[OutcomeCount] | None = Field(
        None,
        description=(
            "Completed sessions grouped by clinical outcome, inside the range. Null for a "
            "caller without the clinical access scope; aggregate or not, outcomes are part "
            "of the clinical record and the wall fails closed."
        ),
    )
