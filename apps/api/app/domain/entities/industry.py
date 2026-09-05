"""
Industry Entity (Aggregate Root)

Represents an industry classification with hierarchical support.
"""

from dataclasses import dataclass, field
from datetime import datetime

from app.domain.events import DomainEvent
from app.domain.exceptions import DomainError, InvariantViolation
from app.domain.value_objects.core import IndustryId, TenantId
from app.shared.utils.datetime import utc_now


@dataclass
class IndustryEntity:
    # Required fields
    id: IndustryId
    tenant_id: TenantId
    name: str
    created_at: datetime
    updated_at: datetime

    # Optional fields
    description: str | None = None
    parent_industry_id: IndustryId | None = None  # For hierarchical structure
    code: str | None = None  # Industry code (e.g., "IT", "HEALTHCARE")
    _is_active: bool = True
    deleted_at: datetime | None = None
    events: list[DomainEvent] = field(default_factory=list[DomainEvent])

    def __post_init__(self) -> None:
        """Validate invariants immediately after construction."""
        self._ensure_invariants()

    # === Behaviors ===

    def update_name(self, name: str) -> None:
        """Update industry name."""
        if self.deleted_at:
            raise DomainError("Cannot update deleted industry")
        if not name:
            raise DomainError("Industry name cannot be empty")
        self.name = name
        self.updated_at = utc_now()

    def update_description(self, description: str | None) -> None:
        """Update industry description."""
        if self.deleted_at:
            raise DomainError("Cannot update deleted industry")
        self.description = description
        self.updated_at = utc_now()

    def set_parent(self, parent_industry_id: IndustryId | None) -> None:
        """Set parent industry (for hierarchy)."""
        if self.deleted_at:
            raise DomainError("Cannot update deleted industry")
        if parent_industry_id == self.id:
            raise DomainError("Industry cannot be its own parent")
        self.parent_industry_id = parent_industry_id
        self.updated_at = utc_now()

    def activate(self) -> None:
        """Activate industry."""
        if self.deleted_at:
            raise DomainError("Cannot activate deleted industry")
        if self._is_active:
            raise DomainError("Industry is already active")
        self._is_active = True
        self.updated_at = utc_now()

    def deactivate(self) -> None:
        """Deactivate industry."""
        if self.deleted_at:
            raise DomainError("Cannot deactivate deleted industry")
        if not self._is_active:
            raise DomainError("Industry is already inactive")
        self._is_active = False
        self.updated_at = utc_now()

    def is_active(self) -> bool:
        """Check if industry is active."""
        return self._is_active and self.deleted_at is None

    # === Invariants ===

    def _ensure_invariants(self) -> None:
        """Ensure industry invariants are met."""
        if not self.name:
            raise InvariantViolation("Industry must have a name")

    # === Public Properties ===
