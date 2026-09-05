"""Domain events for the contract bounded context."""

from dataclasses import dataclass
from datetime import date

from app.domain.events.base import DomainEvent
from app.domain.value_objects.core import ContractId


@dataclass(frozen=True)
class ContractRenewed(DomainEvent):
    """Event raised when a contract is renewed."""

    contract_id: ContractId
    new_end_date: date


@dataclass(frozen=True)
class ContractTerminated(DomainEvent):
    """Event raised when a contract is terminated."""

    contract_id: ContractId
    reason: str


# === Client Events ===
