"""Domain events for organisations, affiliations and historical imports."""

from dataclasses import dataclass
from datetime import date

from app.domain.events.base import DomainEvent
from app.domain.value_objects.core import ProviderId, TenantId, UserId
from app.domain.value_objects.provider_network import (
    PractitionerImportBatchId,
    ProviderAffiliationId,
    ProviderAliasId,
    ProviderOrganisationId,
    ProviderSpecialtyId,
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


@dataclass(frozen=True)
class ProviderAliasResolved(DomainEvent):
    """A person reconciled a source name to a practitioner."""

    alias_id: ProviderAliasId
    tenant_id: TenantId
    source_system: str
    source_value: str
    provider_id: ProviderId
    actor: UserId


@dataclass(frozen=True)
class ProviderAliasRejected(DomainEvent):
    """A person recorded that a source value is not a practitioner."""

    alias_id: ProviderAliasId
    tenant_id: TenantId
    source_system: str
    source_value: str
    actor: UserId
    reason: str


@dataclass(frozen=True)
class ProviderSpecialtyCreated(DomainEvent):
    """Platform-level catalogue change; the vocabulary carries no tenant."""

    specialty_id: ProviderSpecialtyId
    code: str
    label: str
    actor: UserId


@dataclass(frozen=True)
class ProviderSpecialtyRetired(DomainEvent):
    """Platform-level catalogue change; the vocabulary carries no tenant."""

    specialty_id: ProviderSpecialtyId
    code: str
    actor: UserId


@dataclass(frozen=True)
class ProviderSpecialtyRestored(DomainEvent):
    specialty_id: ProviderSpecialtyId
    code: str
    actor: UserId


@dataclass(frozen=True)
class SessionImportBatchAbandoned(DomainEvent):
    batch_id: SessionImportBatchId
    tenant_id: TenantId
    actor: UserId
    reason: str


@dataclass(frozen=True)
class PractitionerImportBatchStaged(DomainEvent):
    batch_id: PractitionerImportBatchId
    tenant_id: TenantId
    source_system: str
    file_hash: str
    row_count: int
    actor: UserId


@dataclass(frozen=True)
class PractitionerImportBatchApplied(DomainEvent):
    batch_id: PractitionerImportBatchId
    tenant_id: TenantId
    created_providers: int
    created_organisations: int
    created_affiliations: int
    failed_rows: int
    actor: UserId
