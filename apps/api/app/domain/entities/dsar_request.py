"""Data Subject Access Request aggregate (Phase 4 #DSAR / SAD §6.6).

Tracks the lifecycle of an export or erasure request. The aggregate is the
*request*, not the data — actual collection / tombstoning is performed by
infrastructure-level use cases that this aggregate gates via its FSM.
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any

from app.domain.enums import DSARRequestStatus, DSARRequestType
from app.domain.events import (
    DomainEvent,
    DSARRequestCompleted,
    DSARRequestSubmitted,
)
from app.domain.exceptions import DomainError, InvalidStateError
from app.domain.value_objects.core import (
    DSARRequestId,
    PersonId,
    TenantId,
    UserId,
)
from app.shared.utils.datetime import utc_now


@dataclass
class DSARRequest:
    """One subject-access request — export OR erasure (never both)."""

    id: DSARRequestId
    tenant_id: TenantId
    subject_person_id: PersonId
    request_type: DSARRequestType
    status: DSARRequestStatus
    requested_by: UserId
    created_at: datetime
    updated_at: datetime
    started_at: datetime | None = None
    completed_at: datetime | None = None
    failed_reason: str | None = None
    output: dict[str, Any] | None = None
    """Export bundle or erasure summary; ``None`` until COMPLETED."""
    erasure_executes_at: datetime | None = None
    """Reversible-window deadline: erasure runs only on/after this time."""
    events: list[DomainEvent] = field(default_factory=list[DomainEvent])

    def __post_init__(self) -> None:
        if self.created_at == self.updated_at and not self.events:
            self.events.append(
                DSARRequestSubmitted(
                    occurred_at=self.created_at,
                    request_id=self.id,
                    tenant_id=self.tenant_id,
                    subject_person_id=self.subject_person_id,
                    request_type=self.request_type.value,
                )
            )

    def start(self, now: datetime | None = None) -> None:
        if self.status != DSARRequestStatus.REQUESTED:
            raise InvalidStateError(f"Cannot start DSAR in status {self.status.value}")
        now = now or utc_now()
        self.status = DSARRequestStatus.PROCESSING
        self.started_at = now
        self.updated_at = now

    def complete(self, output: dict[str, Any], now: datetime | None = None) -> None:
        if self.status != DSARRequestStatus.PROCESSING:
            raise InvalidStateError(f"Cannot complete DSAR in status {self.status.value}")
        now = now or utc_now()
        self.status = DSARRequestStatus.COMPLETED
        self.output = output
        self.completed_at = now
        self.updated_at = now
        self.events.append(
            DSARRequestCompleted(
                occurred_at=now,
                request_id=self.id,
                request_type=self.request_type.value,
            )
        )

    def fail(self, reason: str, now: datetime | None = None) -> None:
        if not reason:
            raise DomainError("Failure requires a reason")
        if self.status not in {
            DSARRequestStatus.REQUESTED,
            DSARRequestStatus.PROCESSING,
        }:
            raise InvalidStateError(f"Cannot fail DSAR in status {self.status.value}")
        now = now or utc_now()
        self.status = DSARRequestStatus.FAILED
        self.failed_reason = reason
        self.updated_at = now

    def cancel(self, now: datetime | None = None) -> None:
        """Subject-initiated cancellation during the reversible window (erasure)."""
        if self.request_type != DSARRequestType.ERASURE:
            raise DomainError("Only erasure requests can be cancelled")
        if self.status not in {
            DSARRequestStatus.REQUESTED,
            DSARRequestStatus.PROCESSING,
        }:
            raise InvalidStateError(f"Cannot cancel DSAR in status {self.status.value}")
        now = now or utc_now()
        if self.erasure_executes_at is not None and now >= self.erasure_executes_at:
            raise DomainError("Reversible window has elapsed; erasure can no longer be cancelled")
        self.status = DSARRequestStatus.CANCELLED
        self.updated_at = now

    def is_within_reversible_window(self, now: datetime | None = None) -> bool:
        if self.erasure_executes_at is None:
            return False
        return (now or utc_now()) < self.erasure_executes_at
