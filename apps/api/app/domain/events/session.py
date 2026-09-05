"""Domain events for the session bounded context."""

from dataclasses import dataclass
from datetime import UTC, datetime

from app.domain.events.base import DomainEvent
from app.domain.value_objects.core import EligibleMemberId, SessionId


@dataclass(frozen=True)
class SessionCompleted(DomainEvent):
    """Event raised when a service session is completed."""

    session_id: SessionId
    member_id: EligibleMemberId


@dataclass(frozen=True)
class SessionCancelled(DomainEvent):
    """Event raised when a service session is cancelled."""

    session_id: SessionId
    reason: str


@dataclass(frozen=True)
class SessionRescheduled(DomainEvent):
    """Event raised when a service session is rescheduled."""

    session_id: SessionId
    new_scheduled_at: datetime

    def __post_init__(self) -> None:
        """Validate that new_scheduled_at is timezone-aware UTC datetime."""
        super().__post_init__()
        if self.new_scheduled_at.tzinfo is None:
            raise ValueError("new_scheduled_at must be timezone-aware")
        if self.new_scheduled_at.tzinfo != UTC:
            raise ValueError(f"new_scheduled_at must be UTC, got {self.new_scheduled_at.tzinfo}")


# === Document Events ===
