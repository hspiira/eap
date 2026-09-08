"""
ServiceAssignment Entity (Aggregate Root)

Represents a link between a service and a contract.
"""

from dataclasses import dataclass, field
from datetime import datetime

from app.domain.enums import BaseStatus
from app.domain.events import (
    DomainEvent,
    ServiceAssignmentCreated,
    ServiceAssignmentStatusChanged,
    ServiceAssignmentUpdated,
)
from app.domain.exceptions import ConflictError, DomainError
from app.domain.value_objects.core import ContractId, ServiceAssignmentId, ServiceId, TenantId
from app.shared.utils.datetime import utc_now


@dataclass
class ServiceAssignmentEntity:
    # Required fields
    id: ServiceAssignmentId
    tenant_id: TenantId
    service_id: ServiceId
    contract_id: ContractId
    status: BaseStatus
    created_at: datetime
    updated_at: datetime

    # Optional fields
    assigned_at: datetime | None = None
    assigned_by: str | None = None  # User ID
    notes: str | None = None
    deleted_at: datetime | None = None
    events: list[DomainEvent] = field(default_factory=list[DomainEvent])

    # === Behaviors ===

    def activate(self) -> None:
        """Activate service assignment."""
        if self.status == BaseStatus.ACTIVE:
            raise ConflictError("Assignment is already active")
        if self.deleted_at:
            raise DomainError("Cannot activate deleted assignment")
        previous = self.status
        self.status = BaseStatus.ACTIVE
        now = utc_now()
        self.assigned_at = now
        self.updated_at = now
        self._record_status_change(previous)

    def deactivate(self) -> None:
        """Deactivate service assignment."""
        if self.status == BaseStatus.INACTIVE:
            raise ConflictError("Assignment is already inactive")
        if self.deleted_at:
            raise DomainError("Cannot deactivate deleted assignment")
        previous = self.status
        self.status = BaseStatus.INACTIVE
        self.updated_at = utc_now()
        self._record_status_change(previous)

    def update_notes(self, notes: str | None) -> None:
        """Update assignment notes."""
        if self.deleted_at:
            raise DomainError("Cannot update deleted assignment")
        self.notes = notes
        self.updated_at = utc_now()
        self.events.append(
            ServiceAssignmentUpdated(
                occurred_at=utc_now(), assignment_id=self.id.value, field="notes"
            )
        )

    def archive(self) -> None:
        """Archive service assignment."""
        if self.deleted_at:
            raise ConflictError("Assignment is already archived")
        previous = self.status
        self.status = BaseStatus.ARCHIVED
        self.updated_at = utc_now()
        self._record_status_change(previous)

    def restore(self) -> None:
        """Restore archived assignment."""
        if not self.deleted_at:
            raise DomainError("Assignment is not archived")
        previous = self.status
        self.deleted_at = None
        self.status = BaseStatus.ACTIVE
        self.updated_at = utc_now()
        self._record_status_change(previous)

    def record_created(self) -> None:
        """Announce this assignment as new. Called by the create use case."""
        self.events.append(
            ServiceAssignmentCreated(
                occurred_at=utc_now(),
                assignment_id=self.id.value,
                contract_id=self.contract_id,
                service_id=self.service_id.value,
            )
        )

    def _record_status_change(self, previous: BaseStatus) -> None:
        """Record a lifecycle move."""
        if previous == self.status:
            return
        self.events.append(
            ServiceAssignmentStatusChanged(
                occurred_at=utc_now(),
                assignment_id=self.id.value,
                from_status=previous.value,
                to_status=self.status.value,
            )
        )

    def is_active(self) -> bool:
        """Check if assignment is active."""
        return self.status == BaseStatus.ACTIVE and self.deleted_at is None

    # === Public Properties ===
