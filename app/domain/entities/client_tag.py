"""
ClientTag Entity (Aggregate Root)

Represents a categorization tag for clients.
"""

import re
from dataclasses import dataclass, field
from datetime import datetime

from app.domain.events import DomainEvent
from app.domain.exceptions import DomainError, InvariantViolation
from app.domain.value_objects.core import ClientTagId, TenantId
from app.shared.utils.datetime import utc_now


@dataclass
class ClientTagEntity:
    # Required fields
    id: ClientTagId
    tenant_id: TenantId
    name: str
    created_at: datetime
    updated_at: datetime

    # Optional fields
    description: str | None = None
    color: str | None = None  # Hex color code for UI display
    _is_active: bool = True
    deleted_at: datetime | None = None
    _events: list[DomainEvent] = field(default_factory=list[DomainEvent])

    def __post_init__(self) -> None:
        """Validate invariants immediately after construction."""
        self._ensure_invariants()

    # === Behaviors ===
    _HEX_COLOR_PATTERN = re.compile(r"^#([A-Fa-f0-9]{6}|[A-Fa-f0-9]{3})$")

    def update_name(self, name: str) -> None:
        """Update tag name."""
        if self.deleted_at:
            raise DomainError("Cannot update deleted tag")
        if not name:
            raise DomainError("Tag name cannot be empty")
        self.name = name
        self.updated_at = utc_now()

    def update_description(self, description: str | None) -> None:
        """Update tag description."""
        if self.deleted_at:
            raise DomainError("Cannot update deleted tag")
        self.description = description
        self.updated_at = utc_now()

    def update_color(self, color: str | None) -> None:
        """Update tag color."""
        if self.deleted_at:
            raise DomainError("Cannot update deleted tag")
        if color and not self._HEX_COLOR_PATTERN.match(color):
            raise DomainError("Color must be a valid hex code (e.g., `#RRGGBB` or `#RGB`)")
        self.color = color
        self.updated_at = utc_now()

    def activate(self) -> None:
        """Activate tag."""
        if self.deleted_at:
            raise DomainError("Cannot activate deleted tag")
        if self._is_active:
            raise DomainError("Tag is already active")
        self._is_active = True
        self.updated_at = utc_now()

    def deactivate(self) -> None:
        """Deactivate tag."""
        if self.deleted_at:
            raise DomainError("Cannot deactivate deleted tag")
        if not self._is_active:
            raise DomainError("Tag is already inactive")
        self._is_active = False
        self.updated_at = utc_now()

    def is_active(self) -> bool:
        """Check if tag is active."""
        return self._is_active and self.deleted_at is None

    # === Invariants ===

    def _ensure_invariants(self) -> None:
        """Ensure tag invariants are met."""
        if not self.name:
            raise InvariantViolation("Tag must have a name")

    # === Public Properties ===
