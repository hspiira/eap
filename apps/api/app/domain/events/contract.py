"""Domain events for the contract bounded context."""

from dataclasses import dataclass
from datetime import date

from app.domain.events.base import DomainEvent
from app.domain.value_objects.core import ClientId, ContractId


@dataclass(frozen=True)
class ContractCreated(DomainEvent):
    """Event raised when a contract is created."""

    contract_id: ContractId
    client_id: ClientId


@dataclass(frozen=True)
class ContractStatusChanged(DomainEvent):
    """Event raised when a contract moves between lifecycle states.

    One event for activate, archive and restore: `map_domain_event_to_audit_action`
    files anything named "...Activated" as a CREATE. See AUDIT_COVERAGE.md.
    """

    contract_id: ContractId
    from_status: str
    to_status: str


@dataclass(frozen=True)
class ContractSigned(DomainEvent):
    """Event raised when a contract is signed."""

    contract_id: ContractId
    signed_by: str


@dataclass(frozen=True)
class ContractUpdated(DomainEvent):
    """Event raised when a contract's commercial terms change.

    `field` names what was touched; the values reach `entity_changes` through
    the handler's diff.
    """

    contract_id: ContractId
    field: str


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
