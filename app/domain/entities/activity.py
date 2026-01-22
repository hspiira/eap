"""
Activity Entity (Aggregate Root)

Represents a client interaction log entry.
"""

from dataclasses import dataclass, field
from datetime import datetime

from app.domain.exceptions import DomainError, InvariantViolation
from app.domain.value_objects.core import ActivityId, TenantId, UserId
from app.shared.utils.datetime import utc_now


@dataclass
class ActivityEntity:
    # Required fields
    _id: ActivityId
    _tenant_id: TenantId
    _client_id: str  # Associated client
    _activity_type: str  # e.g., "CALL", "EMAIL", "MEETING", "NOTE"
    _description: str
    _created_by: UserId
    _occurred_at: datetime
    _created_at: datetime
    _updated_at: datetime
    
    # Optional fields
    _subject: str | None = None
    _outcome: str | None = None
    _next_follow_up: datetime | None = None
    _is_important: bool = False
    _deleted_at: datetime | None = None
    _events: list = field(default_factory=list)
    
    def __post_init__(self) -> None:
        """Validate invariants immediately after construction."""
        self._ensure_invariants()
    
    # === Behaviors ===
    
    def update_description(self, description: str) -> None:
        """Update activity description."""
        if self._deleted_at:
            raise DomainError("Cannot update deleted activity")
        if not description:
            raise DomainError("Activity description cannot be empty")
        self._description = description
        self._updated_at = utc_now()
    
    def update_outcome(self, outcome: str | None) -> None:
        """Update activity outcome."""
        if self._deleted_at:
            raise DomainError("Cannot update deleted activity")
        self._outcome = outcome
        self._updated_at = utc_now()
    
    def set_follow_up(self, next_follow_up: datetime | None) -> None:
        """Set or clear follow-up date."""
        if self._deleted_at:
            raise DomainError("Cannot update deleted activity")
        if next_follow_up and next_follow_up <= utc_now():
            raise DomainError("Follow-up date must be in the future")
        self._next_follow_up = next_follow_up
        self._updated_at = utc_now()
    
    def mark_important(self, is_important: bool) -> None:
        """Mark or unmark activity as important."""
        if self._deleted_at:
            raise DomainError("Cannot update deleted activity")
        self._is_important = is_important
        self._updated_at = utc_now()
    
    # === Invariants ===
    
    def _ensure_invariants(self) -> None:
        """Ensure activity invariants are met."""
        if not self._description:
            raise InvariantViolation("Activity must have a description")
        if not self._activity_type:
            raise InvariantViolation("Activity must have a type")
