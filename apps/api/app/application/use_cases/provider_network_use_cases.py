"""Application operations for organisations and dated affiliations."""

from collections.abc import Sequence
from dataclasses import dataclass
from datetime import date

from app.domain.entities.provider_affiliation import ProviderAffiliationEntity
from app.domain.entities.provider_organisation import ProviderOrganisationEntity
from app.domain.enums.provider_network import OrganisationApprovalStatus
from app.domain.exceptions import DomainError, NotFoundError
from app.domain.repositories.affiliation_attribution_guard import (
    AffiliationAttributionGuard,
)
from app.domain.repositories.provider_network_repository import (
    ProviderAffiliationRepository,
    ProviderOrganisationRepository,
)
from app.domain.value_objects.core import ProviderId, TenantId, UserId
from app.domain.value_objects.provider_network import (
    ProviderAffiliationId,
    ProviderOrganisationId,
)
from app.shared.utils.datetime import utc_now
from app.shared.utils.generators import generate_cuid


class AffiliationOverlapError(DomainError):
    """Raised when a new interval intersects an existing one for the same pair.

    Carries the conflicting affiliation so the route can name it and point the
    caller at the field that conflicts.
    """

    def __init__(self, conflict: ProviderAffiliationEntity, field: str):
        self.conflict = conflict
        self.field = field
        until = conflict.valid_until.isoformat() if conflict.valid_until else "open-ended"
        message = (
            f"Overlaps affiliation {conflict.id.value} "
            f"({conflict.valid_from.isoformat()} to {until})"
        )
        super().__init__(
            message,
            error_code="AFFILIATION_OVERLAP",
            http_status=409,
            details={"field": field, "conflicting_affiliation_id": conflict.id.value},
        )


class AffiliationAttributionConflictError(DomainError):
    """Narrowing the interval would orphan completed session attribution.

    Decision 2 allows rejection or an explicit audited correction. This release
    rejects, because the correction path needs a privileged operation recording
    the prior attribution and reason, and that does not exist yet.
    """

    def __init__(self, session_ids: Sequence[str]):
        self.session_ids = list(session_ids)
        super().__init__(
            f"{len(self.session_ids)} completed session(s) are attributed to this "
            "affiliation beyond the new end date",
            error_code="affiliation_change_would_orphan_attribution",
            http_status=409,
            details={"session_ids": self.session_ids},
        )


@dataclass(frozen=True)
class OrganisationInput:
    name: str
    registration_number: str | None = None
    contact_email: str | None = None
    contact_phone: str | None = None


class CreateOrganisationUseCase:
    def __init__(self, organisations: ProviderOrganisationRepository):
        self._organisations = organisations

    async def execute(
        self, tenant_id: TenantId, data: OrganisationInput, actor: UserId
    ) -> ProviderOrganisationEntity:
        if await self._organisations.name_exists(tenant_id, data.name):
            raise DomainError(f"An organisation named {data.name!r} already exists")
        now = utc_now()
        organisation = ProviderOrganisationEntity(
            id=ProviderOrganisationId(generate_cuid()),
            tenant_id=tenant_id,
            name=data.name.strip(),
            registration_number=data.registration_number,
            contact_email=data.contact_email,
            contact_phone=data.contact_phone,
            created_at=now,
            updated_at=now,
        )
        organisation.record_created(actor)
        await self._organisations.save_organisation(organisation)
        return organisation


class ChangeOrganisationApprovalUseCase:
    """Admin-only supplier approval moves. Authorization is enforced at the route."""

    def __init__(self, organisations: ProviderOrganisationRepository):
        self._organisations = organisations

    async def execute(
        self,
        tenant_id: TenantId,
        organisation_id: ProviderOrganisationId,
        new_status: OrganisationApprovalStatus,
        actor: UserId,
        reason: str,
    ) -> ProviderOrganisationEntity:
        organisation = await self._require(tenant_id, organisation_id)
        organisation.change_approval(new_status, actor, reason)
        await self._organisations.save_organisation(organisation)
        return organisation

    async def _require(
        self, tenant_id: TenantId, organisation_id: ProviderOrganisationId
    ) -> ProviderOrganisationEntity:
        organisation = await self._organisations.get_organisation(tenant_id, organisation_id)
        if organisation is None:
            raise NotFoundError(
                "Provider organisation not found",
                resource_type="ProviderOrganisation",
                resource_id=organisation_id.value,
            )
        return organisation


class SetOrganisationActiveUseCase:
    def __init__(self, organisations: ProviderOrganisationRepository):
        self._organisations = organisations

    async def execute(
        self,
        tenant_id: TenantId,
        organisation_id: ProviderOrganisationId,
        *,
        active: bool,
        actor: UserId,
        reason: str,
    ) -> ProviderOrganisationEntity:
        organisation = await self._organisations.get_organisation(tenant_id, organisation_id)
        if organisation is None:
            raise NotFoundError(
                "Provider organisation not found",
                resource_type="ProviderOrganisation",
                resource_id=organisation_id.value,
            )
        if active:
            organisation.reactivate(actor, reason)
        else:
            organisation.deactivate(actor, reason)
        await self._organisations.save_organisation(organisation)
        return organisation


class CreateAffiliationUseCase:
    """Creates a dated affiliation, rejecting an overlap for the same pair.

    The organisation must exist in the same tenant. The database composite keys
    reject a cross-tenant practitioner or organisation as well; this check is
    here to return a controlled error rather than an integrity failure.
    """

    def __init__(
        self,
        affiliations: ProviderAffiliationRepository,
        organisations: ProviderOrganisationRepository,
    ):
        self._affiliations = affiliations
        self._organisations = organisations

    async def execute(
        self,
        tenant_id: TenantId,
        *,
        provider_id: ProviderId,
        organisation_id: ProviderOrganisationId,
        valid_from: date,
        valid_until: date | None,
        actor: UserId,
    ) -> ProviderAffiliationEntity:
        if await self._organisations.get_organisation(tenant_id, organisation_id) is None:
            raise NotFoundError(
                "Provider organisation not found",
                resource_type="ProviderOrganisation",
                resource_id=organisation_id.value,
            )
        await self._reject_overlap(tenant_id, provider_id, organisation_id, valid_from, valid_until)
        now = utc_now()
        affiliation = ProviderAffiliationEntity(
            id=ProviderAffiliationId(generate_cuid()),
            tenant_id=tenant_id,
            provider_id=provider_id,
            organisation_id=organisation_id,
            valid_from=valid_from,
            valid_until=valid_until,
            created_at=now,
            updated_at=now,
        )
        affiliation.record_created(actor)
        await self._affiliations.save_affiliation(affiliation)
        return affiliation

    async def _reject_overlap(
        self,
        tenant_id: TenantId,
        provider_id: ProviderId,
        organisation_id: ProviderOrganisationId,
        valid_from: date,
        valid_until: date | None,
        *,
        exclude_id: ProviderAffiliationId | None = None,
    ) -> None:
        conflicts = await self._affiliations.find_overlapping(
            tenant_id,
            provider_id,
            organisation_id,
            valid_from=valid_from,
            valid_until=valid_until,
            exclude_id=exclude_id,
        )
        if conflicts:
            raise AffiliationOverlapError(conflicts[0], _conflict_field(conflicts[0], valid_from))


class ChangeAffiliationEndUseCase:
    """Moves only the end date. The practitioner and organisation are immutable.

    The guard is required rather than optional: an omitted check would silently
    invalidate completed attribution, which is the failure decision 2 names.
    """

    def __init__(
        self,
        affiliations: ProviderAffiliationRepository,
        attribution_guard: AffiliationAttributionGuard,
    ):
        self._affiliations = affiliations
        self._attribution_guard = attribution_guard

    async def execute(
        self,
        tenant_id: TenantId,
        affiliation_id: ProviderAffiliationId,
        *,
        valid_until: date | None,
        actor: UserId,
        reason: str,
    ) -> ProviderAffiliationEntity:
        affiliation = await self._affiliations.get_affiliation(tenant_id, affiliation_id)
        if affiliation is None:
            raise NotFoundError(
                "Provider affiliation not found",
                resource_type="ProviderAffiliation",
                resource_id=affiliation_id.value,
            )
        conflicts = await self._affiliations.find_overlapping(
            tenant_id,
            affiliation.provider_id,
            affiliation.organisation_id,
            valid_from=affiliation.valid_from,
            valid_until=valid_until,
            exclude_id=affiliation.id,
        )
        if conflicts:
            raise AffiliationOverlapError(conflicts[0], "valid_until")
        orphaned = await self._attribution_guard.sessions_orphaned_by(
            tenant_id, affiliation_id, new_valid_until=valid_until
        )
        if orphaned:
            raise AffiliationAttributionConflictError(orphaned)
        affiliation.change_end(valid_until, actor, reason)
        await self._affiliations.save_affiliation(affiliation)
        return affiliation


def _conflict_field(conflict: ProviderAffiliationEntity, valid_from: date) -> str:
    """Point at the end date when the new interval starts before the conflict."""
    return "valid_until" if valid_from < conflict.valid_from else "valid_from"
