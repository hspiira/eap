"""Domain events for the client bounded context."""

from dataclasses import dataclass

from app.domain.events.base import DomainEvent
from app.domain.value_objects.core import ClientId, UserId


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
