"""
Industry Entity (Aggregate Root)

Represents an industry classification with hierarchical support.
"""

from dataclasses import dataclass, field
from datetime import datetime

from app.domain.exceptions import DomainError, InvariantViolation
from app.domain.value_objects.core import IndustryId, TenantId
from app.shared.utils.datetime import utc_now


@dataclass
class IndustryEntity:
    # Required fields
    _id: IndustryId
    _tenant_id: TenantId
    _name: str
    _created_at: datetime
    _updated_at: datetime
    
    # Optional fields
    _description: str | None = None
    _parent_industry_id: IndustryId | None = None  # For hierarchical structure
    _code: str | None = None  # Industry code (e.g., "IT", "HEALTHCARE")
    _is_active: bool = True
    _deleted_at: datetime | None = None
    _events: list = field(default_factory=list)
    
    def __post_init__(self) -> None:
        """Validate invariants immediately after construction."""
        self._ensure_invariants()
    
    # === Behaviors ===
    
    def update_name(self, name: str) -> None:
        """Update industry name."""
        if self._deleted_at:
            raise DomainError("Cannot update deleted industry")
        if not name:
            raise DomainError("Industry name cannot be empty")
        self._name = name
        self._updated_at = utc_now()
    
    def update_description(self, description: str | None) -> None:
        """Update industry description."""
        if self._deleted_at:
            raise DomainError("Cannot update deleted industry")
        self._description = description
        self._updated_at = utc_now()
    
    def set_parent(self, parent_industry_id: IndustryId | None) -> None:
        """Set parent industry (for hierarchy)."""
        if self._deleted_at:
            raise DomainError("Cannot update deleted industry")
        if parent_industry_id == self._id:
            raise DomainError("Industry cannot be its own parent")
        self._parent_industry_id = parent_industry_id
        self._updated_at = utc_now()
    
    def activate(self) -> None:
        """Activate industry."""
        if self._deleted_at:
            raise DomainError("Cannot activate deleted industry")
        if self._is_active:
            raise DomainError("Industry is already active")
        self._is_active = True
        self._updated_at = utc_now()
    
    def deactivate(self) -> None:
        """Deactivate industry."""
        if self._deleted_at:
            raise DomainError("Cannot deactivate deleted industry")
        if not self._is_active:
            raise DomainError("Industry is already inactive")
        self._is_active = False
        self._updated_at = utc_now()
    
    def is_active(self) -> bool:
        """Check if industry is active."""
        return self._is_active and self._deleted_at is None
    
    # === Invariants ===
    
    def _ensure_invariants(self) -> None:
        """Ensure industry invariants are met."""
        if not self._name:
            raise InvariantViolation("Industry must have a name")

    # === Public Properties ===

    @property
    def id(self) -> IndustryId:
        return self._id

    @property
    def tenant_id(self) -> TenantId:
        return self._tenant_id

    @property
    def name(self) -> str:
        return self._name

    @property
    def description(self) -> str | None:
        return self._description

    @property
    def parent_industry_id(self) -> IndustryId | None:
        return self._parent_industry_id

    @property
    def code(self) -> str | None:
        return self._code

    @property
    def created_at(self) -> datetime:
        return self._created_at

    @property
    def updated_at(self) -> datetime:
        return self._updated_at

    @property
    def deleted_at(self) -> datetime | None:
        return self._deleted_at
