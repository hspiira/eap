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
    _id: ContactId
    _tenant_id: TenantId
    _client_id: str  # Associated client
    _name: str
    _created_at: datetime
    _updated_at: datetime
    
    # Optional fields
    _title: str | None = None  # Job title
    _email: Email | None = None
    _phone: str | None = None
    _department: str | None = None
    _is_primary: bool = False  # Primary contact for client
    _notes: str | None = None
    _is_active: bool = True
    _deleted_at: datetime | None = None
    _events: list[DomainEvent] = field(default_factory=list)
    
    def __post_init__(self) -> None:
        """Validate invariants immediately after construction."""
        self._ensure_invariants()
    
    # === Behaviors ===
    
    def update_name(self, name: str) -> None:
        """Update contact name."""
        if self._deleted_at:
            raise DomainError("Cannot update deleted contact")
        if not name:
            raise DomainError("Contact name cannot be empty")
        self._name = name
        self._updated_at = utc_now()
    
    def update_contact_info(
        self,
        email: Email | None = None,
        phone: str | None = None,
        title: str | None = None,
        department: str | None = None,
        notes: str | None = None,
    ) -> None:
        """Update contact information."""
        if self._deleted_at:
            raise DomainError("Cannot update deleted contact")
        if email is not None:
            self._email = email
        if phone is not None:
            self._phone = phone
        if title is not None:
            self._title = title
        if department is not None:
            self._department = department
        if notes is not None:
            self._notes = notes
        self._updated_at = utc_now()
        self._ensure_invariants()  # Re-validate after update
    
    def set_primary(self, is_primary: bool) -> None:
        """Set or unset as primary contact."""
        if self._deleted_at:
            raise DomainError("Cannot update deleted contact")
        self._is_primary = is_primary
        self._updated_at = utc_now()
    
    def activate(self) -> None:
        """Activate contact."""
        if self._deleted_at:
            raise DomainError("Cannot activate deleted contact")
        if self._is_active:
            raise DomainError("Contact is already active")
        self._is_active = True
        self._updated_at = utc_now()
    
    def deactivate(self) -> None:
        """Deactivate contact."""
        if self._deleted_at:
            raise DomainError("Cannot deactivate deleted contact")
        if not self._is_active:
            raise DomainError("Contact is already inactive")
        self._is_active = False
        self._updated_at = utc_now()
    
    def is_active(self) -> bool:
        """Check if contact is active."""
        return self._is_active and self._deleted_at is None
    
    # === Invariants ===
    
    def _ensure_invariants(self) -> None:
        """Ensure contact invariants are met."""
        if not self._name:
            raise InvariantViolation("Contact must have a name")
        if not self._email and not self._phone:
            raise InvariantViolation("Contact must have at least email or phone")

    # === Public Properties ===

    @property
    def id(self) -> ContactId:
        return self._id

    @property
    def tenant_id(self) -> TenantId:
        return self._tenant_id

    @property
    def client_id(self) -> str:
        return self._client_id

    @property
    def name(self) -> str:
        return self._name

    @property
    def title(self) -> str | None:
        return self._title

    @property
    def email(self) -> Email | None:
        return self._email

    @property
    def phone(self) -> str | None:
        return self._phone

    @property
    def department(self) -> str | None:
        return self._department

    @property
    def is_primary(self) -> bool:
        return self._is_primary

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
