"""Stage practitioner workbook rows for review. Writes no practitioners.

Nothing staged here is applied: no practitioner, organisation, affiliation or
catalogue entry is created, and the apply step is a separate task. The rules
follow the practitioners review:

- A row whose company column names an organisation stages that organisation
  and an affiliation alongside the practitioner, by name only.
- Names are staged through the provider alias conventions under this
  workbook's source system. A repeated normalised name, on either sheet, makes
  each of its rows a review candidate; identity is never resolved here.
- An organisation name that normalises to the same value as a practitioner's
  own name, anywhere in the batch, is a review candidate too (P-07, P-09):
  the same collision the name-duplicate check catches between two people can
  also happen between a person's own name and a company column that just
  repeats it. Nothing is dropped or reassigned; it is only flagged.
- A cell holding more than one email address and the one Employee contract
  memo are review outcomes with the reason on the row (P-04, P-06). Nothing
  is auto-split and nobody is auto-enrolled.
- Tier, region, panel status and gender are never guessed; salutation stays
  provenance and is never read as gender (P-05).
- Every reason carries a stable code alongside its message (P-10): a
  consumer must never match on the message text.
"""

from collections import defaultdict
from collections.abc import Sequence
from dataclasses import dataclass
from datetime import datetime

from app.domain.entities.practitioner_import import ImportReviewReason
from app.domain.enums.provider_network import ImportReasonCode, PractitionerImportOutcome
from app.domain.repositories.practitioner_import_repository import PractitionerImportRepository
from app.domain.services.provider_alias_normalisation import normalise_practitioner_name
from app.domain.value_objects.core import TenantId
from app.domain.value_objects.provider_network import (
    PractitionerImportBatchId,
    PractitionerImportRowId,
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
    reasons: tuple[ImportReviewReason, ...]
    replay_key: str
    provenance: dict


class PractitionerImportStagingService:
    def __init__(self, imports: PractitionerImportRepository):
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
        staged = []
        for row in rows:
            staged.append(await self._stage_row(tenant_id, file_hash, row, candidates, now))
        return staged

    async def _stage_row(
        self,
        tenant_id: TenantId,
        file_hash: str,
        row: WorkbookRow,
        candidates: dict[str, list[WorkbookRow]],
        now: datetime,
    ) -> StagedPractitionerRow:
        replay_key = _replay_key(row, file_hash)
        existing = await self._imports.find_row_by_replay_key(tenant_id, replay_key)
        if existing is not None:
            reason = ImportReviewReason(
                ImportReasonCode.ALREADY_STAGED,
                f"Already staged as {existing.sheet_name!r} row {existing.row_number} "
                f"of batch {existing.batch_id.value}",
            )
            return _staged(
                row, None, None, PractitionerImportOutcome.DUPLICATE, (reason,), replay_key
            )

        normalized = normalise_practitioner_name(row.raw_name or "")
        if not normalized:
            reason = ImportReviewReason(
                ImportReasonCode.MISSING_NAME, "Source row has no usable practitioner name"
            )
            return _staged(
                row, None, None, PractitionerImportOutcome.REJECTED, (reason,), replay_key
            )

        mapped, reasons = _mapped_profession(row)
        reasons += _candidate_reasons(row, candidates.get(normalized, []))
        reasons += _organisation_collision_reasons(row, candidates)
        reasons += _contact_reasons(row)
        outcome = (
            PractitionerImportOutcome.NEEDS_REVIEW
            if reasons
            else PractitionerImportOutcome.ACCEPTED
        )
        return _staged(row, normalized, mapped, outcome, reasons, replay_key)


def _candidate_index(rows: Sequence[WorkbookRow]) -> dict[str, list[WorkbookRow]]:
    index: dict[str, list[WorkbookRow]] = defaultdict(list)
    for row in rows:
        normalized = normalise_practitioner_name(row.raw_name or "")
        if normalized:
            index[normalized].append(row)
    return index


def _candidate_reasons(
    row: WorkbookRow, group: Sequence[WorkbookRow]
) -> tuple[ImportReviewReason, ...]:
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
        ImportReviewReason(
            ImportReasonCode.DUPLICATE_NAME_CANDIDATE,
            f"Same normalised name as {listed}: candidates for one identity, "
            "to be reconciled by a person, not by staging",
        ),
    )


def _organisation_collision_reasons(
    row: WorkbookRow, candidates: dict[str, list[WorkbookRow]]
) -> tuple[ImportReviewReason, ...]:
    """Flag an organisation column that is really a practitioner's name (P-07, P-09).

    Symmetric to `_candidate_reasons`, but comparing this row's organisation
    against the batch's practitioner names rather than one name against
    another. Catches both a row naming itself and a row naming a different
    practitioner elsewhere in the batch.
    """
    if not row.organisation_name:
        return ()
    normalized_org = normalise_practitioner_name(row.organisation_name)
    matches = candidates.get(normalized_org, []) if normalized_org else []
    if not matches:
        return ()
    this_row = (row.sheet_name, row.row_number)
    if [(peer.sheet_name, peer.row_number) for peer in matches] == [this_row]:
        message = (
            f"Organisation {row.organisation_name!r} is this row's own practitioner "
            "name; confirm this is a real firm, not a person's own name, before "
            "treating it as an organisation"
        )
    else:
        listed = "; ".join(
            f"{peer.sheet_name!r} row {peer.row_number}" for peer in matches[:_CANDIDATE_SAMPLE]
        )
        message = (
            f"Organisation {row.organisation_name!r} matches a practitioner name "
            f"elsewhere in this batch ({listed}); confirm this is a real firm, "
            "not a person's own name, before treating it as an organisation"
        )
    return (ImportReviewReason(ImportReasonCode.ORGANISATION_NAME_COLLISION, message),)


_UNMAPPED_CODE = {
    "PROFESSION": ImportReasonCode.UNMAPPED_PROFESSION,
    "Speciality": ImportReasonCode.UNMAPPED_SPECIALITY,
}


def _mapped_profession(row: WorkbookRow) -> tuple[str | None, tuple[ImportReviewReason, ...]]:
    mapped = map_role(row.profession_column, row.raw_profession)
    if isinstance(mapped, Unmapped):
        code = _UNMAPPED_CODE[mapped.column]
        return None, (
            ImportReviewReason(
                code, f"{mapped.column} value {mapped.value!r} has no entry in the mapping table"
            ),
        )
    return mapped, ()


def _contact_reasons(row: WorkbookRow) -> tuple[ImportReviewReason, ...]:
    reasons = []
    if row.contact_email and row.contact_email.count("@") > 1:
        reasons.append(
            ImportReviewReason(
                ImportReasonCode.MULTI_EMAIL_CELL,
                f"Email cell {row.contact_email!r} holds more than one address; "
                "split by hand at review, never by code",
            )
        )
    if row.contract_memo and row.contract_memo.strip().casefold() == _EMPLOYEE_MEMO:
        reasons.append(
            ImportReviewReason(
                ImportReasonCode.EMPLOYEE_CONTRACT_MEMO,
                "Contract memo says Employee: an employee is not an external "
                "practitioner and must not be enrolled as one without review",
            )
        )
    return tuple(reasons)


def _staged(
    row: WorkbookRow,
    normalized: str | None,
    mapped_profession: str | None,
    outcome: PractitionerImportOutcome,
    reasons: tuple[ImportReviewReason, ...],
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
