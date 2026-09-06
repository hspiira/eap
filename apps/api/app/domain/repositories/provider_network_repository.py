"""Ports for organisations, affiliations, vocabulary, aliases and staged imports."""

from abc import ABC, abstractmethod
from collections.abc import Sequence
from datetime import date, datetime

from app.domain.entities.provider_affiliation import ProviderAffiliationEntity
from app.domain.entities.provider_alias import ProviderAliasEntity
from app.domain.entities.provider_organisation import ProviderOrganisationEntity
from app.domain.entities.provider_specialty import (
    ProviderSpecialtyEntity,
    ProviderSpecialtyLinkEntity,
)
from app.domain.entities.session_import import (
    SessionImportBatchEntity,
    SessionImportRowEntity,
)
from app.domain.value_objects.core import ProviderId, TenantId
from app.domain.value_objects.provider_network import (
    ProviderAffiliationId,
    ProviderAliasId,
    ProviderOrganisationId,
    ProviderSpecialtyId,
    SessionImportBatchId,
)


class ProviderOrganisationRepository(ABC):
    @abstractmethod
    async def get_organisation(
        self, tenant_id: TenantId, organisation_id: ProviderOrganisationId
    ) -> ProviderOrganisationEntity | None:
        """Return the organisation only when it belongs to that tenant.

        Returns None for a cross-tenant or unknown id. Never raises.
        """

    @abstractmethod
    async def list_organisations(
        self,
        tenant_id: TenantId,
        *,
        search: str | None = None,
        is_active: bool | None = None,
        approval_status: str | None = None,
        sort_by: str = "name",
        sort_desc: bool = False,
        limit: int = 20,
        offset: int = 0,
    ) -> tuple[Sequence[ProviderOrganisationEntity], int]:
        """Filtered page plus the full matching count, filtered in SQL."""

    @abstractmethod
    async def get_organisations_by_ids(
        self, tenant_id: TenantId, organisation_ids: Sequence[ProviderOrganisationId]
    ) -> dict[str, ProviderOrganisationEntity]:
        """One query for many organisations, keyed by id.

        Lets an affiliation listing carry organisation labels without a request
        per affiliation.
        """

    @abstractmethod
    async def save_organisation(self, organisation: ProviderOrganisationEntity) -> None: ...

    @abstractmethod
    async def name_exists(
        self,
        tenant_id: TenantId,
        name: str,
        *,
        exclude_id: ProviderOrganisationId | None = None,
    ) -> bool: ...


class ProviderAffiliationRepository(ABC):
    @abstractmethod
    async def get_valid_affiliation(
        self,
        tenant_id: TenantId,
        affiliation_id: ProviderAffiliationId,
        *,
        provider_id: ProviderId,
        at: datetime,
    ) -> ProviderAffiliationEntity | None:
        """Return the affiliation only when it is usable for that delivery.

        Requires the affiliation to belong to that tenant and that
        practitioner, and to cover the day `at` falls on in the provider
        boundary timezone. Validity is start-inclusive and end-exclusive, so
        `at` on `valid_until` does not resolve. Returns None for every other
        case, including not found. Never raises.
        """

    @abstractmethod
    async def get_affiliation(
        self, tenant_id: TenantId, affiliation_id: ProviderAffiliationId
    ) -> ProviderAffiliationEntity | None: ...

    @abstractmethod
    async def find_overlapping(
        self,
        tenant_id: TenantId,
        provider_id: ProviderId,
        organisation_id: ProviderOrganisationId,
        *,
        valid_from: date,
        valid_until: date | None,
        exclude_id: ProviderAffiliationId | None = None,
    ) -> Sequence[ProviderAffiliationEntity]:
        """Existing affiliations for the same pair whose interval intersects."""

    @abstractmethod
    async def list_affiliations(
        self,
        tenant_id: TenantId,
        *,
        provider_id: ProviderId | None = None,
        organisation_id: ProviderOrganisationId | None = None,
        valid_at: date | None = None,
        include_ended: bool = False,
        limit: int = 20,
        offset: int = 0,
    ) -> tuple[Sequence[ProviderAffiliationEntity], int]: ...

    @abstractmethod
    async def save_affiliation(self, affiliation: ProviderAffiliationEntity) -> None: ...


class ProviderSpecialtyRepository(ABC):
    @abstractmethod
    async def get_specialty(
        self, specialty_id: ProviderSpecialtyId
    ) -> ProviderSpecialtyEntity | None: ...

    @abstractmethod
    async def list_specialties(
        self, *, include_inactive: bool = False
    ) -> Sequence[ProviderSpecialtyEntity]: ...

    @abstractmethod
    async def save_specialty(self, specialty: ProviderSpecialtyEntity) -> None: ...

    @abstractmethod
    async def list_links_for_provider(
        self, tenant_id: TenantId, provider_id: ProviderId
    ) -> Sequence[ProviderSpecialtyLinkEntity]:
        """Includes links to retired specialties, which stay readable."""

    @abstractmethod
    async def add_link(self, link: ProviderSpecialtyLinkEntity) -> None: ...

    @abstractmethod
    async def remove_link(self, tenant_id: TenantId, link_id: str) -> bool: ...


class ProviderAliasRepository(ABC):
    @abstractmethod
    async def find_alias(
        self, tenant_id: TenantId, source_system: str, normalized_value: str
    ) -> ProviderAliasEntity | None: ...

    @abstractmethod
    async def get_alias(
        self, tenant_id: TenantId, alias_id: ProviderAliasId
    ) -> ProviderAliasEntity | None: ...

    @abstractmethod
    async def list_aliases(
        self,
        tenant_id: TenantId,
        *,
        source_system: str | None = None,
        state: str | None = None,
        limit: int = 20,
        offset: int = 0,
    ) -> tuple[Sequence[ProviderAliasEntity], int]: ...

    @abstractmethod
    async def save_alias(self, alias: ProviderAliasEntity) -> None: ...


class SessionImportRepository(ABC):
    @abstractmethod
    async def get_batch(
        self, tenant_id: TenantId, batch_id: SessionImportBatchId
    ) -> SessionImportBatchEntity | None: ...

    @abstractmethod
    async def find_batch_by_hash(
        self, tenant_id: TenantId, file_hash: str
    ) -> SessionImportBatchEntity | None:
        """Used to detect a replay of the same file before staging it again."""

    @abstractmethod
    async def save_batch(self, batch: SessionImportBatchEntity) -> None: ...

    @abstractmethod
    async def add_rows(self, rows: Sequence[SessionImportRowEntity], *, file_hash: str) -> None: ...

    @abstractmethod
    async def list_rows(
        self,
        tenant_id: TenantId,
        batch_id: SessionImportBatchId,
        *,
        outcome: str | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> tuple[Sequence[SessionImportRowEntity], int]: ...

    @abstractmethod
    async def mark_row_imported(self, tenant_id: TenantId, row_id: str, session_id: str) -> None:
        """Record which session a staged row produced.

        An update, not a second insert: the row already exists and its replay
        key is unique per tenant.
        """

    @abstractmethod
    async def find_row_by_replay_key(
        self, tenant_id: TenantId, replay_key: str
    ) -> SessionImportRowEntity | None: ...

    @abstractmethod
    async def outcome_counts(
        self, tenant_id: TenantId, batch_id: SessionImportBatchId
    ) -> dict[str, int]:
        """Accepted, duplicate, conflicting and review counts for the batch."""
