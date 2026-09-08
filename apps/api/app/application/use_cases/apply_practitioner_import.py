"""Apply a staged practitioner import batch.

Only Accepted rows create records; NeedsReview, Duplicate and Rejected rows
are untouched, so a batch with zero Accepted rows applies successfully and
creates nothing. Each created record goes through the same audited creation
path the provider module uses: entity factory, creation event, save, audit.

Adopted decisions (recorded in PROVIDERS_MIGRATION.md, 2026-09-07):

- Affiliation ``valid_from`` is the apply day in the provider boundary
  timezone, meaning "affiliated as of import". The workbook carries no dates
  and no historical validity is invented.
- Transaction boundary: one request transaction, one savepoint per row. A
  failing row is rolled back to its savepoint and quarantined as NeedsReview
  with the error recorded; rows already applied are not rolled back, and the
  batch still closes as Applied. An organisation is created in its own
  savepoint, so a later failure in the same row keeps the firm for the rows
  that follow.
- Organisations dedupe case-insensitively by name within the tenant. A created
  organisation arrives with Pending approval: imported paperwork is not
  approval.
- A created practitioner is not bookable: no tier, no region, panel and
  accreditation Pending, no gender. Rates and the contract memo stay in the
  staged row's provenance only; profession does too (P-01's catalogue
  vocabulary is still an open product/clinical decision, so nothing here
  invents a specialty link).
- Adopted 2026-09-07 (P-08): a practitioner's phone number was being computed
  during staging and then dropped at apply, unlike contact_email. Fixed by
  reading it from the row's own provenance rather than adding a new column:
  `CONTACT MOBILE 1` if populated, else `MOBILE CONTACT 2`, first non-blank
  only, never concatenated. This resolves which single number becomes
  `contact_phone`; it does not resolve keeping the second number anywhere
  structured, which stays P-04's open question.
"""

from collections.abc import Callable
from contextlib import AbstractAsyncContextManager
from dataclasses import dataclass
from datetime import datetime
from typing import Any

from app.domain.entities.practitioner_import import PractitionerImportRowEntity
from app.domain.entities.provider import ProviderEntity
from app.domain.entities.provider_affiliation import ProviderAffiliationEntity
from app.domain.entities.provider_organisation import ProviderOrganisationEntity
from app.domain.enums import AccreditationStatus, BaseStatus, PanelStatus
from app.domain.enums.provider_network import (
    ImportBatchStatus,
    ImportReasonCode,
    PractitionerImportOutcome,
)
from app.domain.exceptions import DomainError, NotFoundError
from app.domain.repositories.practitioner_import_repository import PractitionerImportRepository
from app.domain.repositories.provider_network_repository import (
    ProviderAffiliationRepository,
    ProviderOrganisationRepository,
)
from app.domain.repositories.provider_repository import ProviderRepository
from app.domain.services.provider_network_calendar import boundary_day
from app.domain.value_objects.core import ProviderId, ProviderProfile, TenantId, UserId
from app.domain.value_objects.provider_network import (
    PractitionerImportBatchId,
    ProviderAffiliationId,
    ProviderOrganisationId,
)
from app.shared.utils.generators import generate_cuid

SavepointFactory = Callable[[], AbstractAsyncContextManager[Any]]
AuditSink = Callable[[Any], Any]


@dataclass(frozen=True)
class AppliedRow:
    sheet_name: str
    row_number: int
    status: str
    provider_id: str | None = None
    organisation_id: str | None = None
    affiliation_id: str | None = None
    error: str | None = None


@dataclass(frozen=True)
class PractitionerApplyResult:
    created_providers: int
    created_organisations: int
    reused_organisations: int
    created_affiliations: int
    skipped_already_applied: int
    failed: int
    not_applicable: int
    rows: tuple[AppliedRow, ...]


@dataclass
class _Counters:
    providers: int = 0
    organisations: int = 0
    reused: int = 0
    affiliations: int = 0
    skipped: int = 0
    failed: int = 0
    not_applicable: int = 0


class ApplyPractitionerImportUseCase:
    def __init__(
        self,
        imports: PractitionerImportRepository,
        providers: ProviderRepository,
        organisations: ProviderOrganisationRepository,
        affiliations: ProviderAffiliationRepository,
        *,
        savepoint: SavepointFactory,
        audit: AuditSink,
    ):
        self._imports = imports
        self._providers = providers
        self._organisations = organisations
        self._affiliations = affiliations
        self._savepoint = savepoint
        self._audit = audit

    async def execute(
        self,
        tenant_id: TenantId,
        batch_id: PractitionerImportBatchId,
        actor: UserId,
        *,
        now: datetime,
    ) -> PractitionerApplyResult:
        """Create records from every applicable row, then mark the batch applied.

        A batch that is not Staged is refused, so applying twice cannot create
        twice even if the first request is replayed.
        """
        batch = await self._imports.get_batch(tenant_id, batch_id)
        if batch is None:
            raise NotFoundError(
                "Import batch not found",
                resource_type="PractitionerImportBatch",
                resource_id=batch_id.value,
            )
        if batch.status is not ImportBatchStatus.STAGED:
            raise DomainError(
                f"Batch {batch_id.value} is {batch.status.value} and cannot be applied again",
                error_code="import_batch_not_staged",
                http_status=409,
            )

        counters, results = await self._apply_rows(tenant_id, batch_id, actor, now)
        batch.mark_applied(
            actor,
            at=now,
            created_providers=counters.providers,
            created_organisations=counters.organisations,
            created_affiliations=counters.affiliations,
            failed_rows=counters.failed,
        )
        await self._imports.save_batch(batch)
        await self._audit(batch)
        return PractitionerApplyResult(
            created_providers=counters.providers,
            created_organisations=counters.organisations,
            reused_organisations=counters.reused,
            created_affiliations=counters.affiliations,
            skipped_already_applied=counters.skipped,
            failed=counters.failed,
            not_applicable=counters.not_applicable,
            rows=tuple(results),
        )

    async def _apply_rows(
        self,
        tenant_id: TenantId,
        batch_id: PractitionerImportBatchId,
        actor: UserId,
        now: datetime,
    ) -> tuple[_Counters, list[AppliedRow]]:
        counters = _Counters()
        results: list[AppliedRow] = []
        organisations: dict[str, ProviderOrganisationEntity] = {}
        offset = 0
        while True:
            rows, total = await self._imports.list_rows(
                tenant_id, batch_id, limit=200, offset=offset
            )
            if not rows:
                break
            for row in rows:
                result = await self._apply_row(tenant_id, row, actor, now, organisations, counters)
                if result is not None:
                    results.append(result)
            offset += len(rows)
            if offset >= total:
                break
        return counters, results

    async def _apply_row(
        self,
        tenant_id: TenantId,
        row: PractitionerImportRowEntity,
        actor: UserId,
        now: datetime,
        organisations: dict[str, ProviderOrganisationEntity],
        counters: _Counters,
    ) -> AppliedRow | None:
        if row.outcome is not PractitionerImportOutcome.ACCEPTED:
            counters.not_applicable += 1
            return None
        if row.imported_provider_id is not None:
            counters.skipped += 1
            return AppliedRow(
                sheet_name=row.sheet_name,
                row_number=row.row_number,
                status="skipped_already_applied",
                provider_id=row.imported_provider_id,
                organisation_id=row.imported_organisation_id,
                affiliation_id=row.imported_affiliation_id,
            )
        try:
            return await self._create_records(tenant_id, row, actor, now, organisations, counters)
        except Exception as exc:  # noqa: BLE001 - one bad row must not sink the batch
            counters.failed += 1
            row.quarantine(ImportReasonCode.APPLY_FAILED, f"Apply failed: {exc}")
            await self._imports.record_row_apply(row)
            return AppliedRow(
                sheet_name=row.sheet_name,
                row_number=row.row_number,
                status="failed",
                error=str(exc),
            )

    async def _create_records(
        self,
        tenant_id: TenantId,
        row: PractitionerImportRowEntity,
        actor: UserId,
        now: datetime,
        organisations: dict[str, ProviderOrganisationEntity],
        counters: _Counters,
    ) -> AppliedRow:
        organisation = None
        if row.organisation_name:
            async with self._savepoint():
                organisation = await self._resolve_organisation(
                    tenant_id, row.organisation_name, actor, now, organisations, counters
                )
        async with self._savepoint():
            provider = await self._create_provider(tenant_id, row, actor, now)
            affiliation = None
            if organisation is not None:
                affiliation = await self._create_affiliation(
                    tenant_id, provider, organisation, actor, now
                )
            row.mark_applied(
                provider.id.value,
                organisation.id.value if organisation else None,
                affiliation.id.value if affiliation else None,
            )
            await self._imports.record_row_apply(row)
        counters.providers += 1
        if affiliation is not None:
            counters.affiliations += 1
        return AppliedRow(
            sheet_name=row.sheet_name,
            row_number=row.row_number,
            status="applied",
            provider_id=row.imported_provider_id,
            organisation_id=row.imported_organisation_id,
            affiliation_id=row.imported_affiliation_id,
        )

    async def _resolve_organisation(
        self,
        tenant_id: TenantId,
        name: str,
        actor: UserId,
        now: datetime,
        cache: dict[str, ProviderOrganisationEntity],
        counters: _Counters,
    ) -> ProviderOrganisationEntity:
        key = name.strip().lower()
        cached = cache.get(key)
        if cached is not None:
            return cached
        existing = await self._organisations.find_organisation_by_name(tenant_id, name)
        if existing is not None:
            counters.reused += 1
            cache[key] = existing
            return existing
        organisation = ProviderOrganisationEntity(
            id=ProviderOrganisationId(generate_cuid()),
            tenant_id=tenant_id,
            name=name.strip(),
            created_at=now,
            updated_at=now,
        )
        organisation.record_created(actor)
        await self._organisations.save_organisation(organisation)
        await self._audit(organisation)
        counters.organisations += 1
        cache[key] = organisation
        return organisation

    async def _create_provider(
        self,
        tenant_id: TenantId,
        row: PractitionerImportRowEntity,
        actor: UserId,
        now: datetime,
    ) -> ProviderEntity:
        provider = ProviderEntity(
            id=ProviderId(generate_cuid()),
            tenant_id=tenant_id,
            user_id=None,
            display_name=(row.raw_name or "").strip(),
            contact_email=row.contact_email,
            contact_phone=_contact_phone(row),
            status=BaseStatus.PENDING,
            provider_profile=ProviderProfile(
                tier=None,
                region=None,
                accreditation_status=AccreditationStatus.PENDING,
                panel_status=PanelStatus.PENDING,
            ),
            license_info=None,
            created_at=now,
            updated_at=now,
        )
        provider.record_created(actor)
        await self._providers.save(provider)
        await self._audit(provider)
        return provider

    async def _create_affiliation(
        self,
        tenant_id: TenantId,
        provider: ProviderEntity,
        organisation: ProviderOrganisationEntity,
        actor: UserId,
        now: datetime,
    ) -> ProviderAffiliationEntity:
        affiliation = ProviderAffiliationEntity(
            id=ProviderAffiliationId(generate_cuid()),
            tenant_id=tenant_id,
            provider_id=provider.id,
            organisation_id=organisation.id,
            valid_from=boundary_day(now),
            valid_until=None,
            created_at=now,
            updated_at=now,
        )
        affiliation.record_created(actor)
        await self._affiliations.save_affiliation(affiliation)
        await self._audit(affiliation)
        return affiliation


_PHONE_COLUMNS = ("CONTACT MOBILE 1", "MOBILE CONTACT 2")


def _contact_phone(row: PractitionerImportRowEntity) -> str | None:
    """First non-blank of the workbook's two mobile columns (P-08, P-04).

    Only the partner-list sheet carries these columns at all; the consultants
    sheet's provenance simply has neither key. Whichever column is blank is
    skipped rather than treated as a value; the two numbers are never
    concatenated, and the second one, when the first is also present, is not
    promoted anywhere structured.
    """
    for column in _PHONE_COLUMNS:
        value = row.provenance.get(column)
        if value:
            return str(value).strip() or None
    return None
