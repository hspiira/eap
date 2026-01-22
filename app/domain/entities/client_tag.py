"""
ClientTag Entity (Aggregate Root)

Represents a categorization tag for clients.
"""

from dataclasses import dataclass, field
from datetime import datetime

from app.domain.exceptions import DomainError, InvariantViolation
from app.domain.value_objects.core import ClientTagId, TenantId
from app.shared.utils.datetime import utc_now


@dataclass
class ClientTagEntity:
    # Required fields
    _id: ClientTagId
    _tenant_id: TenantId
    _name: str
    _created_at: datetime
    _updated_at: datetime
    
    # Optional fields
    _description: str | None = None
    _color: str | None = None  # Hex color code for UI display
    _is_active: bool = True
    _deleted_at: datetime | None = None
    _events: list = field(default_factory=list)
    
    def __post_init__(self) -> None:
        """Validate invariants immediately after construction."""
        self._ensure_invariants()
    
    # === Behaviors ===
    
    def update_name(self, name: str) -> None:
        """Update tag name."""
        if self._deleted_at:
            raise DomainError("Cannot update deleted tag")
        if not name:
            raise DomainError("Tag name cannot be empty")
        self._name = name
        self._updated_at = utc_now()
    
    def update_description(self, description: str | None) -> None:
        """Update tag description."""
        if self._deleted_at:
            raise DomainError("Cannot update deleted tag")
        self._description = description
        self._updated_at = utc_now()
    
    def update_color(self, color: str | None) -> None:
        """Update tag color."""
        if self._deleted_at:
            raise DomainError("Cannot update deleted tag")
        if color and not color.startswith("#"):
            raise DomainError("Color must be a hex code starting with #")
        self._color = color
        self._updated_at = utc_now()
    
    def activate(self) -> None:
        """Activate tag."""
        if self._deleted_at:
            raise DomainError("Cannot activate deleted tag")
        if self._is_active:
            raise DomainError("Tag is already active")
        self._is_active = True
        self._updated_at = utc_now()
    
    def deactivate(self) -> None:
        """Deactivate tag."""
        if self._deleted_at:
            raise DomainError("Cannot deactivate deleted tag")
        if not self._is_active:
            raise DomainError("Tag is already inactive")
        self._is_active = False
        self._updated_at = utc_now()
    
    def is_active(self) -> bool:
        """Check if tag is active."""
        return self._is_active and self._deleted_at is None
    
    # === Invariants ===
    
    def _ensure_invariants(self) -> None:
        """Ensure tag invariants are met."""
        if not self._name:
            raise InvariantViolation("Tag must have a name")
