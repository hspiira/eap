"""
ServiceAssignment Entity (Aggregate Root)

Represents a link between a service and a contract.
"""

from dataclasses import dataclass, field
from datetime import datetime

from app.domain.enums import BaseStatus
from app.domain.exceptions import DomainError, InvariantViolation
from app.domain.value_objects.core import ServiceAssignmentId, TenantId, ServiceId, ContractId
from app.shared.utils.datetime import utc_now


@dataclass
class ServiceAssignmentEntity:
    # Required fields
    _id: ServiceAssignmentId
    _tenant_id: TenantId
    _service_id: ServiceId
    _contract_id: ContractId
    _status: BaseStatus
    _created_at: datetime
    _updated_at: datetime
    
    # Optional fields
    _assigned_at: datetime | None = None
    _assigned_by: str | None = None  # User ID
    _notes: str | None = None
    _deleted_at: datetime | None = None
    _events: list = field(default_factory=list)
    
    def __post_init__(self) -> None:
        """Validate invariants immediately after construction."""
        self._ensure_invariants()
    
    # === Behaviors ===
    
    def activate(self) -> None:
        """Activate service assignment."""
        if self._status == BaseStatus.ACTIVE:
            raise DomainError("Assignment is already active")
        if self._deleted_at:
            raise DomainError("Cannot activate deleted assignment")
        self._status = BaseStatus.ACTIVE
        now = utc_now()
        self._assigned_at = now
        self._updated_at = now
    
    def deactivate(self) -> None:
        """Deactivate service assignment."""
        if self._status == BaseStatus.INACTIVE:
            raise DomainError("Assignment is already inactive")
        if self._deleted_at:
            raise DomainError("Cannot deactivate deleted assignment")
        self._status = BaseStatus.INACTIVE
        self._updated_at = utc_now()
    
    def update_notes(self, notes: str | None) -> None:
        """Update assignment notes."""
        if self._deleted_at:
            raise DomainError("Cannot update deleted assignment")
        self._notes = notes
        self._updated_at = utc_now()
    
    def is_active(self) -> bool:
        """Check if assignment is active."""
        return self._status == BaseStatus.ACTIVE and self._deleted_at is None
    
    # === Invariants ===
    
    def _ensure_invariants(self) -> None:
        """Ensure assignment invariants are met."""
        # No specific invariants beyond required fields

    # === Public Properties ===

    @property
    def id(self) -> ServiceAssignmentId:
        return self._id

    @property
    def tenant_id(self) -> TenantId:
        return self._tenant_id

    @property
    def service_id(self) -> ServiceId:
        return self._service_id

    @property
    def contract_id(self) -> ContractId:
        return self._contract_id

    @property
    def status(self) -> BaseStatus:
        return self._status

    @property
    def assigned_at(self) -> datetime | None:
        return self._assigned_at

    @property
    def assigned_by(self) -> str | None:
        return self._assigned_by

    @property
    def notes(self) -> str | None:
        return self._notes

    @property
    def created_at(self) -> datetime:
        return self._created_at

    @property
    def updated_at(self) -> datetime:
        return self._updated_at

    @property
    def deleted_at(self) -> datetime | None:
        return self._deleted_at
