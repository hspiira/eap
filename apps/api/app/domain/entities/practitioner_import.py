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

from app.domain.enums.provider_network import (
    ImportBatchStatus,
    ImportReasonCode,
    PractitionerImportOutcome,
)
from app.domain.events import DomainEvent
from app.domain.events.provider_network import (
    PractitionerImportBatchApplied,
    PractitionerImportBatchStaged,
)
from app.domain.exceptions import DomainError
from app.domain.value_objects.core import TenantId, UserId
from app.domain.value_objects.provider_network import (
    PractitionerImportBatchId,
    PractitionerImportRowId,
)

_REVIEW_OUTCOMES = frozenset(
    {PractitionerImportOutcome.NEEDS_REVIEW, PractitionerImportOutcome.REJECTED}
)


@dataclass(frozen=True)
class ImportReviewReason:
    """Why one staged row needs review, applied or apply failed (P-10).

    `code` is the stable, machine-readable part; `message` is prose for
    display. A consumer must never match on `message`.
    """

    code: ImportReasonCode
    message: str


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
    events: list[DomainEvent] = field(default_factory=list["DomainEvent"])

    def __post_init__(self) -> None:
        if not self.file_hash or not self.file_hash.strip():
            raise DomainError("Import batch requires a file hash for provenance")
        if not self.source_system or not self.source_system.strip():
            raise DomainError("Import batch requires a source system")
        if self.row_count < 0:
            raise DomainError("Import batch row count cannot be negative")

    def record_staged(self, actor: UserId) -> None:
        """Emit the staging event so the batch reaches the audit trail."""
        self.events.append(
            PractitionerImportBatchStaged(
                occurred_at=self.created_at,
                batch_id=self.id,
                tenant_id=self.tenant_id,
                source_system=self.source_system,
                file_hash=self.file_hash,
                row_count=self.row_count,
                actor=actor,
            )
        )

    def mark_applied(
        self,
        actor: UserId,
        *,
        at: datetime,
        created_providers: int,
        created_organisations: int,
        created_affiliations: int,
        failed_rows: int,
    ) -> None:
        """Close the batch. A batch that is not Staged refuses a second apply."""
        if self.status is not ImportBatchStatus.STAGED:
            raise DomainError(f"Cannot apply a batch in status {self.status.value}")
        self.status = ImportBatchStatus.APPLIED
        self.applied_by = actor
        self.applied_at = at
        self.updated_at = at
        self.events.append(
            PractitionerImportBatchApplied(
                occurred_at=at,
                batch_id=self.id,
                tenant_id=self.tenant_id,
                created_providers=created_providers,
                created_organisations=created_organisations,
                created_affiliations=created_affiliations,
                failed_rows=failed_rows,
                actor=actor,
            )
        )

    def clear_events(self) -> None:
        self.events.clear()


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
    reasons: tuple[ImportReviewReason, ...] = ()
    provenance: dict[str, str | None] = field(default_factory=dict[str, str | None])
    imported_provider_id: str | None = None
    imported_organisation_id: str | None = None
    imported_affiliation_id: str | None = None

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

    @property
    def is_applicable(self) -> bool:
        """Only an Accepted row not yet applied may create records."""
        return (
            self.outcome is PractitionerImportOutcome.ACCEPTED and self.imported_provider_id is None
        )

    def mark_applied(
        self,
        provider_id: str,
        organisation_id: str | None,
        affiliation_id: str | None,
    ) -> None:
        if self.imported_provider_id is not None:
            raise DomainError(
                f"Row {self.row_number} was already applied as {self.imported_provider_id}"
            )
        self.imported_provider_id = provider_id
        self.imported_organisation_id = organisation_id
        self.imported_affiliation_id = affiliation_id

    def quarantine(self, code: ImportReasonCode, message: str) -> None:
        """Hold a row that failed to apply for a person, never a silent drop."""
        self.imported_provider_id = None
        self.imported_organisation_id = None
        self.imported_affiliation_id = None
        self.outcome = PractitionerImportOutcome.NEEDS_REVIEW
        self.reasons = (*self.reasons, ImportReviewReason(code, message))

    def replay_key(self, file_hash: str) -> str:
        """Idempotency key. Sheet is part of row identity: two sheets share row numbers."""
        return f"file:{file_hash}:sheet:{self.sheet_name}:row:{self.row_number}"
