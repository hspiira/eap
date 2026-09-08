"""Domain events for the client bounded context."""

from dataclasses import dataclass

from app.domain.events.base import DomainEvent
from app.domain.value_objects.core import ClientId, UserId


@dataclass(frozen=True)
class ClientCreated(DomainEvent):
    """Event raised when a client is created."""

    client_id: ClientId
    name: str
    code: str


@dataclass(frozen=True)
class ClientUpdated(DomainEvent):
    """Event raised when a client's stored details change.

    `field` names what was touched. The values are not on the event: the
    handler diffs the entity, so `entity_changes` carries them and this stays
    free of client data.
    """

    client_id: ClientId
    field: str


@dataclass(frozen=True)
class ClientArchived(DomainEvent):
    """Event raised when a client is archived."""

    client_id: ClientId


@dataclass(frozen=True)
class ClientRestored(DomainEvent):
    """Event raised when an archived client is restored."""

    client_id: ClientId


@dataclass(frozen=True)
class ClientVerified(DomainEvent):
    """Event raised when a client is verified."""

    client_id: ClientId
    verified_by: UserId


@dataclass(frozen=True)
class ClientActivated(DomainEvent):
    """Event raised when a client is activated."""

    client_id: ClientId


@dataclass(frozen=True)
class ClientDeactivated(DomainEvent):
    """Event raised when a client is deactivated."""

    client_id: ClientId
    reason: str


@dataclass(frozen=True)
class ClientSuspended(DomainEvent):
    """Event raised when a client is suspended."""

    client_id: ClientId
    reason: str


@dataclass(frozen=True)
class ClientTerminated(DomainEvent):
    """Event raised when a client is terminated."""

    client_id: ClientId
    reason: str


# === Session Events ===
