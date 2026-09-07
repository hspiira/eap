"""Staged practitioner workbook import (P-01, P-03 to P-06).

Staging is review-first: a staged row records what the workbook says and what
normalisation decided; nothing here creates a practitioner, an organisation or
an affiliation. A row that stages an organisation does so by naming it, so the
apply step, when it exists, creates the organisation and affiliation under
review rather than staging inventing either.

Tier, region, panel status and gender have no fields here at all: the workbook
does not supply them and salutation is never read as gender (P-05).
"""

from dataclasses import dataclass, field
from datetime import datetime

from app.domain.enums.provider_network import ImportBatchStatus, PractitionerImportOutcome
from app.domain.exceptions import DomainError
from app.domain.value_objects.core import TenantId, UserId
from app.domain.value_objects.provider_network import (
    PractitionerImportBatchId,
    PractitionerImportRowId,
)

_REVIEW_OUTCOMES = frozenset(
    {PractitionerImportOutcome.NEEDS_REVIEW, PractitionerImportOutcome.REJECTED}
)


@dataclass
class PractitionerImportBatchEntity:
    """Provenance for one workbook staging attempt.

    The workbook has no stable per-row source id, so replay safety is per
    exact file: file hash plus sheet plus worksheet row. A changed file needs
    explicit reconciliation, not automatic deduplication.
    """

    id: PractitionerImportBatchId
    tenant_id: TenantId
    source_system: str
    file_name: str
    file_hash: str
    row_count: int
    staged_by: UserId
    created_at: datetime
    updated_at: datetime
    status: ImportBatchStatus = ImportBatchStatus.STAGED
    applied_by: UserId | None = None
    applied_at: datetime | None = None
    notes: str | None = None

    def __post_init__(self) -> None:
        if not self.file_hash or not self.file_hash.strip():
            raise DomainError("Import batch requires a file hash for provenance")
        if not self.source_system or not self.source_system.strip():
            raise DomainError("Import batch requires a source system")
        if self.row_count < 0:
            raise DomainError("Import batch row count cannot be negative")


@dataclass
class PractitionerImportRowEntity:
    """One workbook row, its staging outcome, and why.

    `provenance` holds every populated source cell verbatim, so unmodelled
    columns (rates, contract memos, second phone, office location,
    salutation) are neither dropped nor merged into modelled fields.
    """

    id: PractitionerImportRowId
    batch_id: PractitionerImportBatchId
    tenant_id: TenantId
    sheet_name: str
    row_number: int
    raw_name: str | None
    normalized_name: str | None
    organisation_name: str | None
    raw_profession: str | None
    mapped_profession: str | None
    contact_email: str | None
    outcome: PractitionerImportOutcome
    created_at: datetime
    reasons: tuple[str, ...] = ()
    provenance: dict = field(default_factory=dict)

    def __post_init__(self) -> None:
        if self.row_number < 1:
            raise DomainError("Import row number is 1-based")
        if not self.sheet_name or not self.sheet_name.strip():
            raise DomainError("Import row requires its sheet name")
        if self.outcome is PractitionerImportOutcome.ACCEPTED and not self.normalized_name:
            raise DomainError("An accepted row requires a normalised practitioner name")
        if self.outcome in _REVIEW_OUTCOMES and not self.reasons:
            raise DomainError("A row held for review must record why")

    @property
    def stages_organisation(self) -> bool:
        """Whether applying this row would also stage an organisation and affiliation."""
        return self.organisation_name is not None

    @property
    def needs_review(self) -> bool:
        return self.outcome in _REVIEW_OUTCOMES

    def replay_key(self, file_hash: str) -> str:
        """Idempotency key. Sheet is part of row identity: two sheets share row numbers."""
        return f"file:{file_hash}:sheet:{self.sheet_name}:row:{self.row_number}"
