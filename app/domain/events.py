"""
Domain Events

Domain events represent something important that happened in the domain.
They are used to communicate state changes between bounded contexts.
"""

from dataclasses import dataclass
from datetime import UTC, datetime
from app.domain.value_objects.core import (
    TenantId, PersonId, UserId, ContractId, ClientId, SessionId, DocumentId
)
from app.domain.enums import PersonType


@dataclass(frozen=True)
class DomainEvent:
    """Base class for all domain events."""
    occurred_at: datetime
    
    def __post_init__(self) -> None:
        """Validate that occurred_at is timezone-aware UTC datetime."""
        if self.occurred_at is None:
            raise ValueError("occurred_at cannot be None")
        if self.occurred_at.tzinfo is None:
            raise ValueError("occurred_at must be timezone-aware")
        if self.occurred_at.tzinfo != UTC:
            raise ValueError(f"occurred_at must be UTC, got {self.occurred_at.tzinfo}")


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


@dataclass(frozen=True)
class PersonSecondaryRoleAdded(DomainEvent):
    """Event raised when a person's secondary role is added."""
    person_id: PersonId
    role: PersonType


@dataclass(frozen=True)
class PersonSecondaryRoleRemoved(DomainEvent):
    """Event raised when a person's secondary role is removed."""
    person_id: PersonId
    role: PersonType


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
    
    def __post_init__(self) -> None:
        """Validate that new_end_date is timezone-aware UTC datetime."""
        super().__post_init__()
        if self.new_end_date is None:
            raise ValueError("new_end_date cannot be None")
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
    
    def __post_init__(self) -> None:
        """Validate that new_scheduled_at is timezone-aware UTC datetime."""
        super().__post_init__()
        if self.new_scheduled_at is None:
            raise ValueError("new_scheduled_at cannot be None")
        if self.new_scheduled_at.tzinfo is None:
            raise ValueError("new_scheduled_at must be timezone-aware")
        if self.new_scheduled_at.tzinfo != UTC:
            raise ValueError(f"new_scheduled_at must be UTC, got {self.new_scheduled_at.tzinfo}")


# === Document Events ===

@dataclass(frozen=True)
class DocumentPublished(DomainEvent):
    """Event raised when a document is published."""
    document_id: DocumentId


@dataclass(frozen=True)
class DocumentArchived(DomainEvent):
    """Event raised when a document is archived."""
    document_id: DocumentId


@dataclass(frozen=True)
class DocumentVersionCreated(DomainEvent):
    """Event raised when a new document version is created."""
    document_id: DocumentId
    new_version_id: DocumentId