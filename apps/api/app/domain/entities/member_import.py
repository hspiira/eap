"""Staged member roster import.

Staging persists what `MemberRowChecker` already decides in memory, so a row
is judged by exactly the same rules whether it lands via the old stateless
preview or this batch. Applying writes rows one at a time and never rolls the
whole batch back on one row's failure; see the "Roster import atomicity"
decision in docs/migrations/MEMBERS_MIGRATION.md.
"""

from dataclasses import dataclass, field
from datetime import datetime

from app.domain.enums.person import MemberImportRowOutcome
from app.domain.enums.provider_network import ImportBatchStatus
from app.domain.events import DomainEvent
from app.domain.events.member import (
    MemberImportBatchAbandoned,
    MemberImportBatchApplied,
    MemberImportBatchStaged,
)
from app.domain.exceptions import DomainError
from app.domain.value_objects.core import ClientId, EligibleMemberId, TenantId, UserId
from app.domain.value_objects.ids import MemberImportBatchId, MemberImportRowId

DECISIONS = frozenset({"import", "skip"})


@dataclass
class MemberImportBatchEntity:
    """Provenance for one roster upload."""

    id: MemberImportBatchId
    tenant_id: TenantId
    file_name: str
    file_hash: str
    row_count: int
    staged_by: UserId
    created_at: datetime
    updated_at: datetime
    status: ImportBatchStatus = ImportBatchStatus.STAGED
    applied_at: datetime | None = None
    applied_by: UserId | None = None
    notes: str | None = None
    events: list[DomainEvent] = field(default_factory=list["DomainEvent"])

    def __post_init__(self) -> None:
        if not self.file_hash or not self.file_hash.strip():
            raise DomainError("Import batch requires a file hash for provenance")
        if not self.file_name or not self.file_name.strip():
            raise DomainError("Import batch requires a file name")
        if self.row_count < 0:
            raise DomainError("Import batch row count cannot be negative")

    def mark_staged(self, *, at: datetime) -> None:
        """Raise the staged event once, after every row has been persisted."""
        self.events.append(
            MemberImportBatchStaged(
                occurred_at=at,
                batch_id=self.id,
                source_file_name=self.file_name,
                row_count=self.row_count,
                actor=self.staged_by,
            )
        )

    def mark_applied(self, actor: UserId, *, at: datetime, accepted_count: int) -> None:
        if self.status is not ImportBatchStatus.STAGED:
            raise DomainError(f"Cannot apply a batch in status {self.status.value}")
        self.status = ImportBatchStatus.APPLIED
        self.applied_by = actor
        self.applied_at = at
        self.updated_at = at
        self.events.append(
            MemberImportBatchApplied(
                occurred_at=at, batch_id=self.id, accepted_count=accepted_count, actor=actor
            )
        )

    def abandon(self, actor: UserId, reason: str, *, at: datetime) -> None:
        if not reason or not reason.strip():
            raise DomainError("Abandoning a batch requires a reason")
        if self.status is ImportBatchStatus.APPLIED:
            raise DomainError("Cannot abandon a batch that has been applied")
        self.status = ImportBatchStatus.ABANDONED
        self.notes = reason
        self.applied_by = actor
        self.updated_at = at
        self.events.append(
            MemberImportBatchAbandoned(occurred_at=at, batch_id=self.id, actor=actor, reason=reason)
        )

    def clear_events(self) -> None:
        self.events.clear()


@dataclass
class MemberImportRowEntity:
    """One roster row, its outcome, and the decision a person made about it.

    `client_code` through `primary_import_source_id` are the raw CSV values,
    persisted so the confirmation step never needs the file resent. They are
    not re-typed as domain value objects here; `MemberRowChecker.check`
    revalidates them from the same `MemberCsvRow` shape it always has.
    """

    id: MemberImportRowId
    batch_id: MemberImportBatchId
    tenant_id: TenantId
    row_number: int
    replay_key: str
    outcome: MemberImportRowOutcome
    decision: str
    created_at: datetime
    client_code: str | None = None
    client_id: ClientId | None = None
    import_source_id: str | None = None
    staff_number: str | None = None
    display_label: str | None = None
    work_email: str | None = None
    personal_email: str | None = None
    gender: str | None = None
    date_of_birth: str | None = None
    phone: str | None = None
    national_id: str | None = None
    passport_number: str | None = None
    status: str | None = None
    relation: str | None = None
    primary_import_source_id: str | None = None
    message: str | None = None
    imported_member_id: EligibleMemberId | None = None

    def __post_init__(self) -> None:
        if self.row_number < 1:
            raise DomainError("Import row number is 1-based")
        if self.decision not in DECISIONS:
            raise DomainError("Row decision must be import or skip")

    @property
    def is_importable(self) -> bool:
        """New, still decided to import, and not already written."""
        return (
            self.outcome is MemberImportRowOutcome.NEW
            and self.decision == "import"
            and self.imported_member_id is None
        )

    def set_decision(self, decision: str) -> None:
        if decision not in DECISIONS:
            raise DomainError("Row decision must be import or skip")
        if self.outcome is not MemberImportRowOutcome.NEW:
            raise DomainError(f"A {self.outcome.value.lower()} row cannot be queued for import")
        self.decision = decision

    def mark_imported(self, member_id: str) -> None:
        if self.imported_member_id is not None:
            raise DomainError(f"Row {self.row_number} was already imported as {member_id}")
        self.imported_member_id = EligibleMemberId(member_id)

    def mark_failed(self, message: str) -> None:
        """A write attempt raised. Terminal: a later apply never retries this row."""
        self.outcome = MemberImportRowOutcome.FAILED
        self.message = message
