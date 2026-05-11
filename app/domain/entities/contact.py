"""
Contact Entity (Aggregate Root)

Represents an additional contact person for a client.
"""

from dataclasses import dataclass, field
from datetime import datetime

from app.domain.events import DomainEvent
from app.domain.exceptions import DomainError, InvariantViolation
from app.domain.value_objects.core import ContactId, TenantId, Email
from app.shared.utils.datetime import utc_now


@dataclass
class ContactEntity:
    # Required fields
    id: ContactId
    tenant_id: TenantId
    client_id: str  # Associated client
    name: str
    created_at: datetime
    updated_at: datetime
    
    # Optional fields
    title: str | None = None  # Job title
    email: Email | None = None
    phone: str | None = None
    department: str | None = None
    is_primary: bool = False  # Primary contact for client
    notes: str | None = None
    _is_active: bool = True
    deleted_at: datetime | None = None
    _events: list[DomainEvent] = field(default_factory=list[DomainEvent])
    
    def __post_init__(self) -> None:
        """Validate invariants immediately after construction."""
        self._ensure_invariants()
    
    # === Behaviors ===
    
    def update_name(self, name: str) -> None:
        """Update contact name."""
        if self.deleted_at:
            raise DomainError("Cannot update deleted contact")
        if not name:
            raise DomainError("Contact name cannot be empty")
        self.name = name
        self.updated_at = utc_now()
    
    def update_contact_info(
        self,
        email: Email | None = None,
        phone: str | None = None,
        title: str | None = None,
        department: str | None = None,
        notes: str | None = None,
    ) -> None:
        """Update contact information."""
        if self.deleted_at:
            raise DomainError("Cannot update deleted contact")
        if email is not None:
            self.email = email
        if phone is not None:
            self.phone = phone
        if title is not None:
            self.title = title
        if department is not None:
            self.department = department
        if notes is not None:
            self.notes = notes
        self.updated_at = utc_now()
        self._ensure_invariants()  # Re-validate after update
    
    def set_primary(self, is_primary: bool) -> None:
        """Set or unset as primary contact."""
        if self.deleted_at:
            raise DomainError("Cannot update deleted contact")
        self.is_primary = is_primary
        self.updated_at = utc_now()
    
    def activate(self) -> None:
        """Activate contact."""
        if self.deleted_at:
            raise DomainError("Cannot activate deleted contact")
        if self._is_active:
            raise DomainError("Contact is already active")
        self._is_active = True
        self.updated_at = utc_now()
    
    def deactivate(self) -> None:
        """Deactivate contact."""
        if self.deleted_at:
            raise DomainError("Cannot deactivate deleted contact")
        if not self._is_active:
            raise DomainError("Contact is already inactive")
        self._is_active = False
        self.updated_at = utc_now()
    
    def is_active(self) -> bool:
        """Check if contact is active."""
        return self._is_active and self.deleted_at is None
    
    # === Invariants ===
    
    def _ensure_invariants(self) -> None:
        """Ensure contact invariants are met."""
        if not self.name:
            raise InvariantViolation("Contact must have a name")
        if not self.email and not self.phone:
            raise InvariantViolation("Contact must have at least email or phone")

    # === Public Properties ===

