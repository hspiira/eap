"""
Domain Events

Domain events represent something important that happened in the domain.
They are used to communicate state changes between bounded contexts.
"""

from dataclasses import dataclass
from datetime import datetime
from app.domain.value_objects.core import (
    TenantId, PersonId, UserId, ContractId, ClientId, SessionId
)
from app.domain.enums import PersonType


@dataclass(frozen=True)
class DomainEvent:
    """Base class for all domain events."""
    occurred_at: datetime


@dataclass(frozen=True)
class TenantActivated(DomainEvent):
    """Event raised when a tenant is activated."""
    tenant_id: TenantId


@dataclass(frozen=True)
class TenantSuspended(DomainEvent):
    """Event raised when a tenant is suspended."""
    tenant_id: TenantId
    reason: str


@dataclass(frozen=True)
class TenantTerminated(DomainEvent):
    """Event raised when a tenant is terminated."""
    tenant_id: TenantId
    reason: str


# === Person Events ===

@dataclass(frozen=True)
class PersonActivated(DomainEvent):
    """Event raised when a person is activated."""
    person_id: PersonId
    person_type: PersonType


@dataclass(frozen=True)
class PersonDeactivated(DomainEvent):
    """Event raised when a person is deactivated."""
    person_id: PersonId
    reason: str | None = None


@dataclass(frozen=True)
class PersonTerminated(DomainEvent):
    """Event raised when a person is terminated."""
    person_id: PersonId
    reason: str


# === User Events ===

@dataclass(frozen=True)
class UserActivated(DomainEvent):
    """Event raised when a user is activated."""
    user_id: UserId


@dataclass(frozen=True)
class UserSuspended(DomainEvent):
    """Event raised when a user is suspended."""
    user_id: UserId
    reason: str


@dataclass(frozen=True)
class UserBanned(DomainEvent):
    """Event raised when a user is banned."""
    user_id: UserId
    reason: str


@dataclass(frozen=True)
class UserEmailVerified(DomainEvent):
    """Event raised when a user's email is verified."""
    user_id: UserId


@dataclass(frozen=True)
class UserDeactivated(DomainEvent):
    """Event raised when a user is deactivated."""
    user_id: UserId
    reason: str | None = None


@dataclass(frozen=True)
class UserTerminated(DomainEvent):
    """Event raised when a user is terminated."""
    user_id: UserId
    reason: str


# === Contract Events ===

@dataclass(frozen=True)
class ContractRenewed(DomainEvent):
    """Event raised when a contract is renewed."""
    contract_id: ContractId
    new_end_date: datetime


@dataclass(frozen=True)
class ContractTerminated(DomainEvent):
    """Event raised when a contract is terminated."""
    contract_id: ContractId
    reason: str


# === Client Events ===

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

@dataclass(frozen=True)
class SessionCompleted(DomainEvent):
    """Event raised when a service session is completed."""
    session_id: SessionId
    person_id: PersonId


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
