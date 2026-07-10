"""
Activity Entity (Aggregate Root)

Represents a client interaction log entry.
"""

from dataclasses import dataclass, field
from datetime import datetime

from app.domain.events import DomainEvent
from app.domain.exceptions import DomainError, InvariantViolation
from app.domain.value_objects.core import ActivityId, TenantId, UserId
from app.shared.utils.datetime import utc_now


@dataclass
class ActivityEntity:
    # Required fields
    id: ActivityId
    tenant_id: TenantId
    client_id: str  # Associated client
    activity_type: str  # e.g., "CALL", "EMAIL", "MEETING", "NOTE"
    description: str
    created_by: UserId
    occurred_at: datetime
    created_at: datetime
    updated_at: datetime
    
    # Optional fields
    subject: str | None = None
    outcome: str | None = None
    next_follow_up: datetime | None = None
    is_important: bool = False
    deleted_at: datetime | None = None
    _events: list[DomainEvent] = field(default_factory=list[DomainEvent])
    
    def __post_init__(self) -> None:
        """Validate invariants immediately after construction."""
        self._ensure_invariants()
    
    # === Behaviors ===
    
    def update_description(self, description: str) -> None:
        """Update activity description."""
        if self.deleted_at:
            raise DomainError("Cannot update deleted activity")
        if not description:
            raise DomainError("Activity description cannot be empty")
        self.description = description
        self.updated_at = utc_now()
    
    def update_outcome(self, outcome: str | None) -> None:
        """Update activity outcome."""
        if self.deleted_at:
            raise DomainError("Cannot update deleted activity")
        self.outcome = outcome
        self.updated_at = utc_now()
    
    def set_follow_up(self, next_follow_up: datetime | None) -> None:
        """Set or clear follow-up date."""
        if self.deleted_at:
            raise DomainError("Cannot update deleted activity")
        if next_follow_up and next_follow_up <= utc_now():
            raise DomainError("Follow-up date must be in the future")
        self.next_follow_up = next_follow_up
        self.updated_at = utc_now()
    
    def mark_important(self, is_important: bool) -> None:
        """Mark or unmark activity as important."""
        if self.deleted_at:
            raise DomainError("Cannot update deleted activity")
        self.is_important = is_important
        self.updated_at = utc_now()
    
    # === Invariants ===
    
    def _ensure_invariants(self) -> None:
        """Ensure activity invariants are met."""
        if not self.description:
            raise InvariantViolation("Activity must have a description")
        if not self.activity_type:
            raise InvariantViolation("Activity must have a type")

    # === Public Properties ===

