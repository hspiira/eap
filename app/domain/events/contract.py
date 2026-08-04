"""Domain events for the contract bounded context."""

from dataclasses import dataclass
from datetime import UTC, datetime

from app.domain.events.base import DomainEvent
from app.domain.value_objects.core import ContractId


@dataclass(frozen=True)
class ContractRenewed(DomainEvent):
    """Event raised when a contract is renewed."""

    contract_id: ContractId
    new_end_date: datetime

    def __post_init__(self) -> None:
        """Validate that new_end_date is timezone-aware UTC datetime."""
        super().__post_init__()
        if self.new_end_date.tzinfo is None:
            raise ValueError("new_end_date must be timezone-aware")
        if self.new_end_date.tzinfo != UTC:
            raise ValueError(f"new_end_date must be UTC, got {self.new_end_date.tzinfo}")


@dataclass(frozen=True)
class ContractTerminated(DomainEvent):
    """Event raised when a contract is terminated."""

    contract_id: ContractId
    reason: str


# === Client Events ===
