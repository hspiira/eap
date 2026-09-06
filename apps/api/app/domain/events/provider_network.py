"""Domain events for organisations, affiliations and historical imports."""

from dataclasses import dataclass
from datetime import date

from app.domain.events.base import DomainEvent
from app.domain.value_objects.core import ProviderId, TenantId, UserId
from app.domain.value_objects.provider_network import (
    ProviderAffiliationId,
    ProviderOrganisationId,
    SessionImportBatchId,
)


@dataclass(frozen=True)
class ProviderOrganisationCreated(DomainEvent):
    organisation_id: ProviderOrganisationId
    tenant_id: TenantId
    name: str
    actor: UserId


@dataclass(frozen=True)
class ProviderOrganisationApprovalChanged(DomainEvent):
    organisation_id: ProviderOrganisationId
    tenant_id: TenantId
    old_status: str
    new_status: str
    actor: UserId
    reason: str


@dataclass(frozen=True)
class ProviderOrganisationDeactivated(DomainEvent):
    organisation_id: ProviderOrganisationId
    tenant_id: TenantId
    actor: UserId
    reason: str


@dataclass(frozen=True)
class ProviderAffiliationCreated(DomainEvent):
    affiliation_id: ProviderAffiliationId
    tenant_id: TenantId
    provider_id: ProviderId
    organisation_id: ProviderOrganisationId
    valid_from: date
    valid_until: date | None
    actor: UserId


@dataclass(frozen=True)
class ProviderAffiliationEnded(DomainEvent):
    """The affiliation's end date moved. Endpoints themselves never change."""

    affiliation_id: ProviderAffiliationId
    tenant_id: TenantId
    old_valid_until: date | None
    new_valid_until: date | None
    actor: UserId
    reason: str


@dataclass(frozen=True)
class SessionImportBatchStaged(DomainEvent):
    batch_id: SessionImportBatchId
    tenant_id: TenantId
    source_system: str
    file_hash: str
    row_count: int
    actor: UserId


@dataclass(frozen=True)
class SessionImportBatchApplied(DomainEvent):
    batch_id: SessionImportBatchId
    tenant_id: TenantId
    accepted_count: int
    actor: UserId
