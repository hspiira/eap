"""Base domain event."""

from dataclasses import dataclass
from datetime import UTC, datetime


@dataclass(frozen=True)
class DomainEvent:
    """Base class for all domain events."""

    occurred_at: datetime

    def __post_init__(self) -> None:
        """Validate that occurred_at is timezone-aware UTC datetime."""
        if self.occurred_at.tzinfo is None:
            raise ValueError("occurred_at must be timezone-aware")
        if self.occurred_at.tzinfo != UTC:
            raise ValueError(f"occurred_at must be UTC, got {self.occurred_at.tzinfo}")
