"""Dashboard API contracts.

One aggregate, tenant-scoped read model for the home page. Every figure is a
count or a small grouped series; no record-level data leaves this endpoint,
so it discloses nothing a list endpoint would not.

Delivered work means completed sessions. Scheduled bookings are not delivery
and are deliberately absent from the trend; a booking pipeline would be its
own series with its own name.
"""

from pydantic import BaseModel, Field


class DashboardKpis(BaseModel):
    """Headline counts for the KPI strip."""

    sessions_90d: int = Field(..., description="Completed sessions in the last 90 days")
    sessions_prior_90d: int = Field(
        ..., description="Completed sessions in the 90 days before that, for the delta"
    )
    clients_served_90d: int = Field(
        ..., description="Distinct clients with a completed session in the last 90 days"
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


class MonthlySessions(BaseModel):
    """One month of completed sessions. The series is always 12 entries, zero-filled."""

    month: str = Field(..., description="Calendar month, YYYY-MM")
    total: int


class CategoryCount(BaseModel):
    """Completed sessions per session category over the trend window."""

    category: str
    total: int


class ClientSessions(BaseModel):
    """Completed sessions per client over the trend window."""

    client_id: str
    client_name: str
    total: int


class ImportQueueEntry(BaseModel):
    """One unresolved outcome bucket in the current import batch."""

    outcome: str
    total: int


class ImportBatchSummary(BaseModel):
    """The batch the backlog figures describe."""

    file_name: str
    status: str
    row_count: int
    accepted: int
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

    kpis: DashboardKpis
    sessions_monthly: list[MonthlySessions]
    sessions_by_category: list[CategoryCount]
    top_clients: list[ClientSessions]
    import_queues: list[ImportQueueEntry]
    import_batch: ImportBatchSummary | None = Field(
        None, description="Absent when the tenant has never staged an import"
    )
    data_quality: DataQuality
