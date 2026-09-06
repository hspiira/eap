"""Stage historical session rows for review. Writes no sessions.

Decision 7 keeps historical acceptance separate from booking eligibility: a row
may name a practitioner who is suspended or unaccredited today, because the
delivery already happened. What it may not do is create future work, so a row
dated after the import day is rejected rather than staged as acceptable.

Applying a staged batch is not implemented here. It requires the historical
write entry point agent 1 owns, and calling the live session use case would
merge the two rule sets that this separation exists to keep apart.
"""

from dataclasses import dataclass
from datetime import date, datetime

from app.application.services.provider_alias_reconciliation import (
    NameOutcome,
    NameResolution,
    ProviderAliasReconciliationService,
)
from app.domain.enums.provider_network import DeliveryContext, ImportRowOutcome
from app.domain.repositories.provider_network_repository import (
    ProviderAffiliationRepository,
    SessionImportRepository,
)
from app.domain.services.provider_network_calendar import boundary_day
from app.domain.value_objects.core import TenantId
from app.domain.value_objects.provider_network import (
    ProviderAffiliationId,
    SessionImportBatchId,
    SessionImportRowId,
)
from app.shared.utils.generators import generate_cuid

_NAME_OUTCOMES = {
    NameOutcome.MISSING: ImportRowOutcome.MISSING_PRACTITIONER,
    NameOutcome.UNMAPPED: ImportRowOutcome.UNMAPPED_PRACTITIONER,
    NameOutcome.AMBIGUOUS: ImportRowOutcome.AMBIGUOUS_PRACTITIONER,
    NameOutcome.REJECTED: ImportRowOutcome.REJECTED,
}


@dataclass(frozen=True)
class SourceRow:
    """One parsed source row. Deliberately free of any live session shape."""

    row_number: int
    raw_practitioner_name: str | None
    session_date: date | None
    source_record_key: str | None = None
    organisation_affiliation_id: str | None = None


@dataclass(frozen=True)
class StagedRow:
    """The outcome for one source row, ready to persist."""

    row_number: int
    outcome: ImportRowOutcome
    delivery_context: DeliveryContext
    provider_id: object | None
    provider_affiliation_id: ProviderAffiliationId | None
    reasons: tuple[str, ...]
    replay_key: str
    source_record_key: str | None
    raw_practitioner_name: str | None
    session_date: date | None


class SessionImportStagingService:
    def __init__(
        self,
        aliases: ProviderAliasReconciliationService,
        affiliations: ProviderAffiliationRepository,
        imports: SessionImportRepository,
    ):
        self._aliases = aliases
        self._affiliations = affiliations
        self._imports = imports

    async def stage_row(
        self,
        tenant_id: TenantId,
        source_system: str,
        file_hash: str,
        row: SourceRow,
        *,
        now: datetime,
    ) -> StagedRow:
        replay_key = _replay_key(row, file_hash)
        existing = await self._imports.find_row_by_replay_key(tenant_id, replay_key)
        if existing is not None:
            return self._staged(
                row,
                ImportRowOutcome.DUPLICATE,
                DeliveryContext.UNKNOWN,
                None,
                None,
                (
                    f"Already staged as row {existing.row_number} of batch {existing.batch_id.value}",
                ),
                replay_key,
            )

        if row.session_date is None:
            return self._held(
                row, ImportRowOutcome.REJECTED, ("Source row has no date",), replay_key
            )
        if row.session_date > boundary_day(now):
            return self._held(
                row,
                ImportRowOutcome.REJECTED,
                (
                    f"Session date {row.session_date.isoformat()} is in the future; "
                    "the historical path cannot create a booking",
                ),
                replay_key,
            )

        resolution = await self._aliases.resolve(
            tenant_id, source_system, row.raw_practitioner_name
        )
        if not resolution.is_resolved:
            return self._held(
                row, _NAME_OUTCOMES[resolution.outcome], resolution.reasons, replay_key
            )

        return await self._with_delivery_context(tenant_id, row, resolution, replay_key, now=now)

    async def _with_delivery_context(
        self,
        tenant_id: TenantId,
        row: SourceRow,
        resolution: NameResolution,
        replay_key: str,
        *,
        now: datetime,
    ) -> StagedRow:
        """Organisation context needs a valid affiliation; otherwise stay unknown.

        Decision 2 forbids reading an absent organisation as direct delivery, so
        a row with no supplier evidence is staged as unknown rather than direct.
        """
        if row.organisation_affiliation_id is None:
            return self._staged(
                row,
                ImportRowOutcome.ACCEPTED,
                DeliveryContext.UNKNOWN,
                resolution.provider_id,
                None,
                (),
                replay_key,
            )
        at = datetime.combine(row.session_date, datetime.min.time(), tzinfo=now.tzinfo)
        affiliation = await self._affiliations.get_valid_affiliation(
            tenant_id,
            ProviderAffiliationId(row.organisation_affiliation_id),
            provider_id=resolution.provider_id,
            at=at,
        )
        if affiliation is None:
            return self._held(
                row,
                ImportRowOutcome.CONFLICTING,
                (
                    f"Affiliation {row.organisation_affiliation_id} is not valid for this "
                    f"practitioner on {row.session_date.isoformat()}",
                ),
                replay_key,
            )
        return self._staged(
            row,
            ImportRowOutcome.ACCEPTED,
            DeliveryContext.ORGANISATION,
            resolution.provider_id,
            affiliation.id,
            (),
            replay_key,
        )

    def _held(
        self,
        row: SourceRow,
        outcome: ImportRowOutcome,
        reasons: tuple[str, ...],
        replay_key: str,
    ) -> StagedRow:
        return self._staged(row, outcome, DeliveryContext.UNKNOWN, None, None, reasons, replay_key)

    def _staged(
        self,
        row: SourceRow,
        outcome: ImportRowOutcome,
        context: DeliveryContext,
        provider_id: object | None,
        affiliation_id: ProviderAffiliationId | None,
        reasons: tuple[str, ...],
        replay_key: str,
    ) -> StagedRow:
        return StagedRow(
            row_number=row.row_number,
            outcome=outcome,
            delivery_context=context,
            provider_id=provider_id,
            provider_affiliation_id=affiliation_id,
            reasons=reasons,
            replay_key=replay_key,
            source_record_key=row.source_record_key,
            raw_practitioner_name=row.raw_practitioner_name,
            session_date=row.session_date,
        )


def _replay_key(row: SourceRow, file_hash: str) -> str:
    if row.source_record_key:
        return f"key:{row.source_record_key}"
    return f"file:{file_hash}:row:{row.row_number}"


def new_row_id() -> SessionImportRowId:
    return SessionImportRowId(generate_cuid())


def new_batch_id() -> SessionImportBatchId:
    return SessionImportBatchId(generate_cuid())
