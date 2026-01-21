"""
Domain Events

Domain events represent something important that happened in the domain.
They are used to communicate state changes between bounded contexts.
"""

from dataclasses import dataclass
from datetime import datetime
from app.domain.value_objects.core import TenantId


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
