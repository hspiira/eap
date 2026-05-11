"""Historical session import validator (Phase 4 #D-Import / SAD §11 risk).

Idempotent, dry-run-capable validator for the cleaned Excel → DB load (≈ 5,253
historical sessions). The pure validator below produces an ``ImportReport`` from
a sequence of raw input rows + a ``CanonicalMappings`` lookup. Whether to commit
the accepted rows is a decision left to the caller (CLI / route) so the same
validator backs both ``--dry-run`` reporting and the actual write path.

Idempotency:
    Each input row carries a stable ``source_id`` derived from upstream
    Excel coordinates (sheet + row number, or workbook-assigned uuid). Rows
    whose ``source_id`` already appears in ``existing_source_ids`` are
    classified ``REJECTED_DUPLICATE`` rather than re-inserted, so re-running
    the import after a partial failure is safe.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date, datetime
from enum import Enum
from typing import Iterable

from app.domain.enums import SessionStatus


class ImportClassification(str, Enum):
    """Per-row classification produced by the validator."""

    ACCEPTED = "Accepted"
    REJECTED_UNMAPPED_CLIENT = "RejectedUnmappedClient"
    REJECTED_UNMAPPED_SERVICE = "RejectedUnmappedService"
    REJECTED_UNMAPPED_PROVIDER = "RejectedUnmappedProvider"
    REJECTED_UNMAPPED_PERSON = "RejectedUnmappedPerson"
    REJECTED_UNMAPPED_STATUS = "RejectedUnmappedStatus"
    REJECTED_INVALID_DATE = "RejectedInvalidDate"
    REJECTED_DUPLICATE = "RejectedDuplicate"
    REJECTED_MISSING_FIELD = "RejectedMissingField"


@dataclass(frozen=True)
class CanonicalMappings:
    """Code → canonical id lookup tables for the cleaned import.

    Each map is *exhaustive* for the set of values that should appear in the
    legacy data; unmapped values are *intentionally* rejected so the operator
    notices missing canonical entries before the import runs.
    """

    client_codes: dict[str, str] = field(default_factory=dict)
    service_codes: dict[str, str] = field(default_factory=dict)
    provider_codes: dict[str, str] = field(default_factory=dict)
    person_codes: dict[str, str] = field(default_factory=dict)
    status_text: dict[str, SessionStatus] = field(default_factory=dict)


@dataclass(frozen=True)
class HistoricalSessionRow:
    """One raw input row read from the source spreadsheet.

    ``source_id`` is the idempotency key. The other fields hold the *codes*
    the spreadsheet uses (e.g. client short-codes); the validator resolves
    them through ``CanonicalMappings``.
    """

    source_id: str
    client_code: str
    service_code: str
    provider_code: str
    person_code: str
    status_text: str
    scheduled_at_text: str
    notes: str | None = None


@dataclass
class AcceptedRow:
    """Row that passed validation; carries the canonical IDs ready to insert."""

    source_id: str
    client_id: str
    service_id: str
    provider_id: str
    person_id: str
    status: SessionStatus
    scheduled_at: datetime
    notes: str | None


@dataclass
class RejectedRow:
    """Row that failed validation; carries the original + the failure reason."""

    source_id: str
    classification: ImportClassification
    detail: str
    raw: HistoricalSessionRow


@dataclass
class ImportReport:
    accepted: list[AcceptedRow] = field(default_factory=list[AcceptedRow])
    rejected: list[RejectedRow] = field(default_factory=list[RejectedRow])

    @property
    def accepted_count(self) -> int:
        return len(self.accepted)

    @property
    def rejected_count(self) -> int:
        return len(self.rejected)

    def rejection_summary(self) -> dict[str, int]:
        out: dict[str, int] = {}
        for r in self.rejected:
            key = r.classification.value
            out[key] = out.get(key, 0) + 1
        return out

    def to_summary(self) -> dict[str, object]:
        return {
            "accepted_count": self.accepted_count,
            "rejected_count": self.rejected_count,
            "total": self.accepted_count + self.rejected_count,
            "rejection_summary": self.rejection_summary(),
        }


def _parse_datetime(value: str) -> datetime | None:
    """Accept ISO date or ISO datetime; reject everything else."""
    if not value:
        return None
    try:
        return datetime.fromisoformat(value)
    except ValueError:
        try:
            return datetime.combine(date.fromisoformat(value), datetime.min.time())
        except ValueError:
            return None


def validate_row(
    row: HistoricalSessionRow,
    mappings: CanonicalMappings,
    existing_source_ids: set[str],
) -> AcceptedRow | RejectedRow:
    """Pure-function classifier. No DB access, no IO."""
    if not row.source_id:
        return RejectedRow(
            source_id=row.source_id or "",
            classification=ImportClassification.REJECTED_MISSING_FIELD,
            detail="source_id is empty",
            raw=row,
        )
    if row.source_id in existing_source_ids:
        return RejectedRow(
            source_id=row.source_id,
            classification=ImportClassification.REJECTED_DUPLICATE,
            detail=f"source_id={row.source_id} already imported",
            raw=row,
        )
    for field_name, value in {
        "client_code": row.client_code,
        "service_code": row.service_code,
        "provider_code": row.provider_code,
        "person_code": row.person_code,
        "status_text": row.status_text,
        "scheduled_at_text": row.scheduled_at_text,
    }.items():
        if not value:
            return RejectedRow(
                source_id=row.source_id,
                classification=ImportClassification.REJECTED_MISSING_FIELD,
                detail=f"{field_name} is empty",
                raw=row,
            )

    client_id = mappings.client_codes.get(row.client_code)
    if client_id is None:
        return RejectedRow(
            source_id=row.source_id,
            classification=ImportClassification.REJECTED_UNMAPPED_CLIENT,
            detail=f"No canonical client for code '{row.client_code}'",
            raw=row,
        )
    service_id = mappings.service_codes.get(row.service_code)
    if service_id is None:
        return RejectedRow(
            source_id=row.source_id,
            classification=ImportClassification.REJECTED_UNMAPPED_SERVICE,
            detail=f"No canonical service for code '{row.service_code}'",
            raw=row,
        )
    provider_id = mappings.provider_codes.get(row.provider_code)
    if provider_id is None:
        return RejectedRow(
            source_id=row.source_id,
            classification=ImportClassification.REJECTED_UNMAPPED_PROVIDER,
            detail=f"No canonical provider for code '{row.provider_code}'",
            raw=row,
        )
    person_id = mappings.person_codes.get(row.person_code)
    if person_id is None:
        return RejectedRow(
            source_id=row.source_id,
            classification=ImportClassification.REJECTED_UNMAPPED_PERSON,
            detail=f"No canonical person for code '{row.person_code}'",
            raw=row,
        )
    status = mappings.status_text.get(row.status_text)
    if status is None:
        return RejectedRow(
            source_id=row.source_id,
            classification=ImportClassification.REJECTED_UNMAPPED_STATUS,
            detail=f"No status mapping for '{row.status_text}'",
            raw=row,
        )
    scheduled_at = _parse_datetime(row.scheduled_at_text)
    if scheduled_at is None:
        return RejectedRow(
            source_id=row.source_id,
            classification=ImportClassification.REJECTED_INVALID_DATE,
            detail=f"Cannot parse '{row.scheduled_at_text}' as ISO date/datetime",
            raw=row,
        )
    return AcceptedRow(
        source_id=row.source_id,
        client_id=client_id,
        service_id=service_id,
        provider_id=provider_id,
        person_id=person_id,
        status=status,
        scheduled_at=scheduled_at,
        notes=row.notes,
    )


def validate_rows(
    rows: Iterable[HistoricalSessionRow],
    mappings: CanonicalMappings,
    existing_source_ids: set[str] | None = None,
) -> ImportReport:
    """Batch entrypoint. Tracks already-seen source_ids within the batch too,
    so duplicates inside a single import file are caught the same way as
    re-imports from a previous run."""
    seen = set(existing_source_ids or set())
    report = ImportReport()
    for row in rows:
        outcome = validate_row(row, mappings, seen)
        if isinstance(outcome, AcceptedRow):
            report.accepted.append(outcome)
            seen.add(outcome.source_id)
        else:
            report.rejected.append(outcome)
    return report
