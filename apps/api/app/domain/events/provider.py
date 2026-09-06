"""Domain events for the provider bounded context."""

from dataclasses import dataclass

from app.domain.events.base import DomainEvent
from app.domain.value_objects.core import ClientId, ProviderId, UserId


@dataclass(frozen=True)
class ProviderPanelStatusChanged(DomainEvent):
    """Audit trail for the 80→8 panel cull and any other panel-status moves."""

    provider_id: ProviderId
    old_status: str
    new_status: str
    actor: UserId
    reason: str


@dataclass(frozen=True)
class ProviderTierChanged(DomainEvent):
    """Audit trail for provider tier upgrades / downgrades."""

    provider_id: ProviderId
    old_tier: str
    new_tier: str
    actor: UserId
    reason: str


@dataclass(frozen=True)
class ProviderAssignmentBlocked(DomainEvent):
    """Raised when an assignment is rejected by panel or non-compete enforcement."""

    provider_id: ProviderId
    client_id: ClientId
    reason: str
