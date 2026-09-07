"""Stage historical session rows for review. Writes no sessions.

Decision 7 keeps historical acceptance separate from booking eligibility: a row
may name a practitioner who is suspended or unaccredited today, because the
delivery already happened. What it may not do is create future work, so a row
dated after the import day is rejected rather than staged as acceptable.

Applying a staged batch is not implemented here. It requires the historical
write entry point agent 1 owns, and calling the live session use case would
merge the two rule sets that this separation exists to keep apart.
"""

from collections import defaultdict
from collections.abc import Sequence
from dataclasses import dataclass
from datetime import date, datetime

from app.application.services.provider_alias_reconciliation import (
    NameOutcome,
    NameResolution,
    ProviderAliasReconciliationService,
)
from app.domain.enums.provider_network import DeliveryContext, ImportRowOutcome
from app.domain.exceptions import DomainError
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

SOURCE_KEY_STRATEGY = "source_record_key"
FILE_ROW_KEY_STRATEGY = "file:{hash}:row:{n}"

_SAMPLE_SIZE = 3


@dataclass(frozen=True)
class SourceRow:
    """One parsed source row. Deliberately free of any live session shape."""

    row_number: int
    raw_practitioner_name: str | None
    session_date: date | None
    source_record_key: str | None = None
    organisation_affiliation_id: str | None = None
    member_id: str | None = None
    service_id: str | None = None


@dataclass(frozen=True)
class StagedRow:
    """The outcome for one source row, ready to persist."""

    row_number: int
    outcome: ImportRowOutcome
    delivery_context: DeliveryContext
    provider_id: object | None
    provider_affiliation_id: ProviderAffiliationId | None
    member_id: str | None
    service_id: str | None
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

        unresolved = _unresolved_subject(row)
        if unresolved is not None:
            outcome, reason = unresolved
            return self._held(row, outcome, (reason,), replay_key)

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
            member_id=row.member_id if outcome is ImportRowOutcome.ACCEPTED else None,
            service_id=row.service_id if outcome is ImportRowOutcome.ACCEPTED else None,
            reasons=reasons,
            replay_key=replay_key,
            source_record_key=row.source_record_key,
            raw_practitioner_name=row.raw_practitioner_name,
            session_date=row.session_date,
        )


def _unresolved_subject(row: SourceRow) -> tuple[ImportRowOutcome, str] | None:
    """Whether the row still lacks a member or a service.

    The write path requires both and staging cannot invent them. Member
    identity belongs to the members migration and service identity to the
    catalogue, so an unresolved one is quarantined here rather than guessed.
    Kept as two outcomes because they need different people to resolve them.
    """
    if row.member_id is None:
        return (
            ImportRowOutcome.UNRESOLVED_MEMBER,
            "No member resolved for this row; member reconciliation is not built",
        )
    if row.service_id is None:
        return (
            ImportRowOutcome.UNRESOLVED_SERVICE,
            "No service resolved for this row; service reconciliation is not built",
        )
    return None


def _replay_key(row: SourceRow, file_hash: str) -> str:
    if row.source_record_key:
        return f"key:{row.source_record_key}"
    return f"file:{file_hash}:row:{row.row_number}"


def replay_key_strategy(source_record_key_field: str | None) -> str:
    """Which replay key form a batch is keyed by.

    The batch records the column it was keyed on, or nothing, so a later
    reconciliation reading a stored batch can name the strategy without the
    file. `SessionImportBatchModel.source_record_key_field` is that record.
    """
    return SOURCE_KEY_STRATEGY if source_record_key_field else FILE_ROW_KEY_STRATEGY


def preflight_source_keys(rows: Sequence[SourceRow], source_record_key_field: str | None) -> str:
    """Check a nominated key column over the whole file and name the strategy.

    Runs before any row is staged. A repeated key makes `_replay_key` collide,
    and the second row is staged as Duplicate and lost without a rejection an
    operator would think to look at.
    """
    if source_record_key_field:
        _refuse_unusable_key(rows, source_record_key_field)
    return replay_key_strategy(source_record_key_field)


def _refuse_unusable_key(rows: Sequence[SourceRow], column: str) -> None:
    """Uniqueness and completeness are both required, because a blank fails open.

    A row with no key falls back to `file:{hash}:row:{n}` while its neighbours
    use `key:{...}`, leaving one batch keyed two ways: a re-export under a new
    hash then restages exactly those rows and returns the rest as duplicates.
    """
    collisions = _colliding_keys(rows)
    blanks = tuple(row.row_number for row in rows if not row.source_record_key)
    if not collisions and not blanks:
        return
    raise DomainError(
        _preflight_message(column, collisions, blanks),
        error_code="IMPORT_SOURCE_KEY_NOT_UNIQUE",
        http_status=422,
        details={"source_record_key_field": column},
    )


def _colliding_keys(rows: Sequence[SourceRow]) -> tuple[tuple[str, tuple[int, ...]], ...]:
    grouped: dict[str, list[int]] = defaultdict(list)
    for row in rows:
        if row.source_record_key:
            grouped[row.source_record_key].append(row.row_number)
    return tuple((key, tuple(numbers)) for key, numbers in grouped.items() if len(numbers) > 1)


def _preflight_message(
    column: str,
    collisions: tuple[tuple[str, tuple[int, ...]], ...],
    blanks: tuple[int, ...],
) -> str:
    parts = [f"Column {column!r} cannot be the source record key."]
    if collisions:
        affected = sum(len(numbers) for _, numbers in collisions)
        parts.append(
            f"Repeated values: {len(collisions)} across {affected} rows, "
            f"for example {_collision_sample(collisions)}."
        )
    if blanks:
        parts.append(f"Rows with no value: {len(blanks)}, for example {_row_sample(blanks)}.")
    return " ".join(parts)


def _collision_sample(collisions: tuple[tuple[str, tuple[int, ...]], ...]) -> str:
    return "; ".join(
        f"{key!r} on rows {_row_sample(numbers)}" for key, numbers in collisions[:_SAMPLE_SIZE]
    )


def _row_sample(numbers: tuple[int, ...]) -> str:
    return ", ".join(str(number) for number in numbers[:_SAMPLE_SIZE])


def new_row_id() -> SessionImportRowId:
    return SessionImportRowId(generate_cuid())


def new_batch_id() -> SessionImportBatchId:
    return SessionImportBatchId(generate_cuid())
