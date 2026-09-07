"""Stage practitioner workbook rows for review. Writes no practitioners.

Nothing staged here is applied: no practitioner, organisation, affiliation or
catalogue entry is created, and the apply step is a separate task. The rules
follow the practitioners review:

- A row whose company column names an organisation stages that organisation
  and an affiliation alongside the practitioner, by name only.
- Names are staged through the provider alias conventions under this
  workbook's source system. A repeated normalised name, on either sheet, makes
  each of its rows a review candidate; identity is never resolved here.
- A cell holding more than one email address and the one Employee contract
  memo are review outcomes with the reason on the row (P-04, P-06). Nothing
  is auto-split and nobody is auto-enrolled.
- Tier, region, panel status and gender are never guessed; salutation stays
  provenance and is never read as gender (P-05).
"""

from collections import defaultdict
from collections.abc import Sequence
from dataclasses import dataclass
from datetime import datetime

from app.domain.entities.provider_alias import ProviderAliasEntity
from app.domain.enums.provider_network import PractitionerImportOutcome
from app.domain.repositories.practitioner_import_repository import PractitionerImportRepository
from app.domain.repositories.provider_network_repository import ProviderAliasRepository
from app.domain.services.provider_alias_normalisation import normalise_practitioner_name
from app.domain.value_objects.core import TenantId
from app.domain.value_objects.provider_network import (
    PractitionerImportBatchId,
    PractitionerImportRowId,
    ProviderAliasId,
)
from app.shared.utils.generators import generate_cuid
from app.shared.utils.practitioner_workbook import WorkbookRow
from app.shared.utils.practitioner_workbook_normalisation import Unmapped, map_role

WORKBOOK_SOURCE_SYSTEM = "practitioners-orgs-workbook"

FILE_SHEET_ROW_KEY = "file:{hash}:sheet:{sheet}:row:{n}"

_EMPLOYEE_MEMO = "employee"

_CANDIDATE_SAMPLE = 5


@dataclass(frozen=True)
class StagedPractitionerRow:
    """The staging outcome for one workbook row, ready to persist."""

    sheet_name: str
    row_number: int
    raw_name: str | None
    normalized_name: str | None
    organisation_name: str | None
    raw_profession: str | None
    mapped_profession: str | None
    contact_email: str | None
    outcome: PractitionerImportOutcome
    reasons: tuple[str, ...]
    replay_key: str
    provenance: dict


class PractitionerImportStagingService:
    def __init__(self, aliases: ProviderAliasRepository, imports: PractitionerImportRepository):
        self._aliases = aliases
        self._imports = imports

    async def stage_rows(
        self,
        tenant_id: TenantId,
        file_hash: str,
        rows: Sequence[WorkbookRow],
        *,
        now: datetime,
    ) -> list[StagedPractitionerRow]:
        """Stage every parsed row, sharing one identity-candidate index."""
        candidates = _candidate_index(rows)
        ensured: set[str] = set()
        staged = []
        for row in rows:
            staged.append(
                await self._stage_row(tenant_id, file_hash, row, candidates, ensured, now)
            )
        return staged

    async def _stage_row(
        self,
        tenant_id: TenantId,
        file_hash: str,
        row: WorkbookRow,
        candidates: dict[str, list[WorkbookRow]],
        ensured: set[str],
        now: datetime,
    ) -> StagedPractitionerRow:
        replay_key = _replay_key(row, file_hash)
        existing = await self._imports.find_row_by_replay_key(tenant_id, replay_key)
        if existing is not None:
            reason = (
                f"Already staged as {existing.sheet_name!r} row {existing.row_number} "
                f"of batch {existing.batch_id.value}"
            )
            return _staged(
                row, None, None, PractitionerImportOutcome.DUPLICATE, (reason,), replay_key
            )

        normalized = normalise_practitioner_name(row.raw_name or "")
        if not normalized:
            return _staged(
                row,
                None,
                None,
                PractitionerImportOutcome.REJECTED,
                ("Source row has no usable practitioner name",),
                replay_key,
            )

        await self._ensure_alias(tenant_id, row, normalized, ensured, now)
        mapped, reasons = _mapped_profession(row)
        reasons += _candidate_reasons(row, candidates.get(normalized, []))
        reasons += _contact_reasons(row)
        outcome = (
            PractitionerImportOutcome.NEEDS_REVIEW
            if reasons
            else PractitionerImportOutcome.ACCEPTED
        )
        return _staged(row, normalized, mapped, outcome, reasons, replay_key)

    async def _ensure_alias(
        self,
        tenant_id: TenantId,
        row: WorkbookRow,
        normalized: str,
        ensured: set[str],
        now: datetime,
    ) -> None:
        """Record the source name as an unmapped alias if nobody has yet.

        An existing alias is left exactly as a person decided it; staging never
        resolves, rejects or re-opens one.
        """
        if normalized in ensured:
            return
        ensured.add(normalized)
        existing = await self._aliases.find_alias(tenant_id, WORKBOOK_SOURCE_SYSTEM, normalized)
        if existing is not None:
            return
        await self._aliases.save_alias(
            ProviderAliasEntity(
                id=ProviderAliasId(generate_cuid()),
                tenant_id=tenant_id,
                source_system=WORKBOOK_SOURCE_SYSTEM,
                source_value=row.raw_name or "",
                normalized_value=normalized,
                created_at=now,
                updated_at=now,
            )
        )


def _candidate_index(rows: Sequence[WorkbookRow]) -> dict[str, list[WorkbookRow]]:
    index: dict[str, list[WorkbookRow]] = defaultdict(list)
    for row in rows:
        normalized = normalise_practitioner_name(row.raw_name or "")
        if normalized:
            index[normalized].append(row)
    return index


def _candidate_reasons(row: WorkbookRow, group: Sequence[WorkbookRow]) -> tuple[str, ...]:
    others = [
        peer
        for peer in group
        if (peer.sheet_name, peer.row_number) != (row.sheet_name, row.row_number)
    ]
    if not others:
        return ()
    listed = "; ".join(
        f"{peer.sheet_name!r} row {peer.row_number}" for peer in others[:_CANDIDATE_SAMPLE]
    )
    return (
        f"Same normalised name as {listed}: candidates for one identity, "
        "to be reconciled by a person, not by staging",
    )


def _mapped_profession(row: WorkbookRow) -> tuple[str | None, tuple[str, ...]]:
    mapped = map_role(row.profession_column, row.raw_profession)
    if isinstance(mapped, Unmapped):
        return None, (f"{mapped.column} value {mapped.value!r} has no entry in the mapping table",)
    return mapped, ()


def _contact_reasons(row: WorkbookRow) -> tuple[str, ...]:
    reasons = []
    if row.contact_email and row.contact_email.count("@") > 1:
        reasons.append(
            f"Email cell {row.contact_email!r} holds more than one address; "
            "split by hand at review, never by code"
        )
    if row.contract_memo and row.contract_memo.strip().casefold() == _EMPLOYEE_MEMO:
        reasons.append(
            "Contract memo says Employee: an employee is not an external "
            "practitioner and must not be enrolled as one without review"
        )
    return tuple(reasons)


def _staged(
    row: WorkbookRow,
    normalized: str | None,
    mapped_profession: str | None,
    outcome: PractitionerImportOutcome,
    reasons: tuple[str, ...],
    replay_key: str,
) -> StagedPractitionerRow:
    contact_email = row.contact_email
    if contact_email and contact_email.count("@") > 1:
        contact_email = None
    return StagedPractitionerRow(
        sheet_name=row.sheet_name,
        row_number=row.row_number,
        raw_name=row.raw_name,
        normalized_name=normalized,
        organisation_name=row.organisation_name,
        raw_profession=row.raw_profession,
        mapped_profession=mapped_profession,
        contact_email=contact_email,
        outcome=outcome,
        reasons=reasons,
        replay_key=replay_key,
        provenance=dict(row.provenance),
    )


def _replay_key(row: WorkbookRow, file_hash: str) -> str:
    return f"file:{file_hash}:sheet:{row.sheet_name}:row:{row.row_number}"


def new_batch_id() -> PractitionerImportBatchId:
    return PractitionerImportBatchId(generate_cuid())


def new_row_id() -> PractitionerImportRowId:
    return PractitionerImportRowId(generate_cuid())
