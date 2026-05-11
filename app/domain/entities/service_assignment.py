"""
ServiceAssignment Entity (Aggregate Root)

Represents a link between a service and a contract.
"""

from dataclasses import dataclass, field
from datetime import datetime

from app.domain.enums import BaseStatus
from app.domain.events import DomainEvent
from app.domain.exceptions import DomainError
from app.domain.value_objects.core import ServiceAssignmentId, TenantId, ServiceId, ContractId
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
    _events: list[DomainEvent] = field(default_factory=list)
    
    # === Behaviors ===
    
    def activate(self) -> None:
        """Activate service assignment."""
        if self.status == BaseStatus.ACTIVE:
            raise DomainError("Assignment is already active")
        if self.deleted_at:
            raise DomainError("Cannot activate deleted assignment")
        self.status = BaseStatus.ACTIVE
        now = utc_now()
        self.assigned_at = now
        self.updated_at = now
    
    def deactivate(self) -> None:
        """Deactivate service assignment."""
        if self.status == BaseStatus.INACTIVE:
            raise DomainError("Assignment is already inactive")
        if self.deleted_at:
            raise DomainError("Cannot deactivate deleted assignment")
        self.status = BaseStatus.INACTIVE
        self.updated_at = utc_now()
    
    def update_notes(self, notes: str | None) -> None:
        """Update assignment notes."""
        if self.deleted_at:
            raise DomainError("Cannot update deleted assignment")
        self.notes = notes
        self.updated_at = utc_now()
    
    def archive(self) -> None:
        """Archive service assignment."""
        if self.deleted_at:
            raise DomainError("Assignment is already archived")
        self.status = BaseStatus.ARCHIVED
        self.updated_at = utc_now()
    
    def restore(self) -> None:
        """Restore archived assignment."""
        if not self.deleted_at:
            raise DomainError("Assignment is not archived")
        self.deleted_at = None
        self.status = BaseStatus.ACTIVE
        self.updated_at = utc_now()
    
    def is_active(self) -> bool:
        """Check if assignment is active."""
        return self.status == BaseStatus.ACTIVE and self.deleted_at is None
    
    # === Public Properties ===

