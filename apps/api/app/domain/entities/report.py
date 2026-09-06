"""Report template + run entities (Phase 2 #D-Reports / SAD §5.2.10)."""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any

from app.domain.enums import ReportQueryType, ReportRunStatus
from app.domain.events import DomainEvent
from app.domain.exceptions import ConflictError, DomainError
from app.domain.value_objects.core import (
    ReportRunId,
    ReportTemplateId,
    TenantId,
    UserId,
)
from app.shared.utils.datetime import utc_now


@dataclass(frozen=True)
class TemplateSection:
    """One section of a report template: a query + display metadata."""

    title: str
    query_type: ReportQueryType
    parameters: dict[str, Any] = field(default_factory=dict[str, Any])
    narrative: str | None = None

    def __post_init__(self) -> None:
        if not self.title:
            raise DomainError("TemplateSection requires a title")


@dataclass
class ReportTemplate:
    """A reusable report shape composed of one or more query sections."""

    id: ReportTemplateId
    tenant_id: TenantId
    code: str
    name: str
    sections: list[TemplateSection]
    is_active: bool
    created_at: datetime
    updated_at: datetime
    description: str | None = None

    def __post_init__(self) -> None:
        if not self.code:
            raise DomainError("ReportTemplate requires a code")
        if not self.name:
            raise DomainError("ReportTemplate requires a name")
        if not self.sections:
            raise DomainError("ReportTemplate must contain at least one section")

    def deactivate(self) -> None:
        if not self.is_active:
            raise ConflictError("ReportTemplate is already inactive")
        self.is_active = False
        self.updated_at = utc_now()

    def activate(self) -> None:
        if self.is_active:
            raise ConflictError("ReportTemplate is already active")
        self.is_active = True
        self.updated_at = utc_now()


@dataclass
class ReportRun:
    """Materialised execution of a :class:`ReportTemplate`."""

    id: ReportRunId
    tenant_id: TenantId
    template_id: ReportTemplateId
    requested_by: UserId
    parameters: dict[str, Any]
    status: ReportRunStatus
    created_at: datetime
    updated_at: datetime
    started_at: datetime | None = None
    completed_at: datetime | None = None
    output: dict[str, Any] | None = None
    error: str | None = None
    events: list[DomainEvent] = field(default_factory=list[DomainEvent])

    def mark_running(self, now: datetime | None = None) -> None:
        if self.status != ReportRunStatus.PENDING:
            raise DomainError(f"Cannot start run in status {self.status.value}")
        now = now or utc_now()
        self.status = ReportRunStatus.RUNNING
        self.started_at = now
        self.updated_at = now

    def mark_completed(self, output: dict[str, Any], now: datetime | None = None) -> None:
        if self.status != ReportRunStatus.RUNNING:
            raise DomainError(f"Cannot complete run in status {self.status.value}")
        now = now or utc_now()
        self.status = ReportRunStatus.COMPLETED
        self.output = output
        self.completed_at = now
        self.updated_at = now

    def mark_failed(self, error: str, now: datetime | None = None) -> None:
        if self.status not in {ReportRunStatus.PENDING, ReportRunStatus.RUNNING}:
            raise DomainError(f"Cannot fail run in status {self.status.value}")
        if not error:
            raise DomainError("Failure requires an error message")
        now = now or utc_now()
        self.status = ReportRunStatus.FAILED
        self.error = error
        self.completed_at = now
        self.updated_at = now
