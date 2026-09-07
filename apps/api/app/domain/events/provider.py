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


@dataclass(frozen=True)
class ProviderCreated(DomainEvent):
    """A practitioner record was created."""

    provider_id: ProviderId
    actor: UserId


@dataclass(frozen=True)
class ProviderProfileUpdated(DomainEvent):
    """Ordinary contact and profile fields changed, outside the lifecycle commands."""

    provider_id: ProviderId
    changed_fields: tuple[str, ...]
    actor: UserId


@dataclass(frozen=True)
class ProviderAccreditationChanged(DomainEvent):
    """Audit trail for accreditation status, authority and expiry changes."""

    provider_id: ProviderId
    old_status: str
    new_status: str
    old_expiry: str | None
    new_expiry: str | None
    actor: UserId
    reason: str


@dataclass(frozen=True)
class ProviderStatusChanged(DomainEvent):
    """Audit trail for activating or deactivating a practitioner record."""

    provider_id: ProviderId
    old_status: str
    new_status: str
    actor: UserId
    reason: str


@dataclass(frozen=True)
class ProviderAccountLinked(DomainEvent):
    """An Admin linked a user account to a practitioner."""

    provider_id: ProviderId
    user_id: UserId
    actor: UserId
    reason: str


@dataclass(frozen=True)
class ProviderAccountUnlinked(DomainEvent):
    """An Admin removed the user account link from a practitioner."""

    provider_id: ProviderId
    user_id: UserId
    actor: UserId
    reason: str


@dataclass(frozen=True)
class ProviderEngagementDocumentRecorded(DomainEvent):
    """An engagement-document checklist entry was written or changed."""

    provider_id: ProviderId
    document_kind: str
    old_state: str | None
    new_state: str
    note: str | None
    actor: UserId
