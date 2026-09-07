"""Staged historical session import (decision 7, import acceptance section).

Staging is deliberately separate from live booking. A staged row records what
the source says and what reconciliation decided; nothing here writes a session.
"""

from dataclasses import dataclass, field
from datetime import date, datetime

from app.domain.enums import (
    ClientType,
    SessionAttendance,
    SessionCategory,
    SessionClinicalStatus,
    SessionStatus,
    SessionType,
)
from app.domain.enums.provider_network import (
    DeliveryContext,
    ImportBatchStatus,
    ImportRowOutcome,
)
from app.domain.events import DomainEvent
from app.domain.events.provider_network import (
    SessionImportBatchAbandoned,
    SessionImportBatchApplied,
)
from app.domain.exceptions import DomainError
from app.domain.value_objects.core import ProviderId, TenantId, UserId
from app.domain.value_objects.provider_network import (
    ProviderAffiliationId,
    SessionImportBatchId,
    SessionImportRowId,
)

_REVIEW_OUTCOMES = frozenset(
    {
        ImportRowOutcome.MISSING_PRACTITIONER,
        ImportRowOutcome.UNMAPPED_PRACTITIONER,
        ImportRowOutcome.AMBIGUOUS_PRACTITIONER,
        ImportRowOutcome.UNRESOLVED_MEMBER,
        ImportRowOutcome.UNRESOLVED_SERVICE,
        ImportRowOutcome.CONFLICTING,
        ImportRowOutcome.REJECTED,
    }
)


@dataclass
class SessionImportBatchEntity:
    """Provenance for one import attempt.

    `file_hash` plus a row number is the replay key when the source has no
    stable record id. It makes replaying the same file safe and says nothing
    about a changed file, which needs explicit reconciliation.
    """

    id: SessionImportBatchId
    tenant_id: TenantId
    source_system: str
    file_name: str
    file_hash: str
    row_count: int
    staged_by: UserId
    created_at: datetime
    updated_at: datetime
    status: ImportBatchStatus = ImportBatchStatus.STAGED
    source_record_key_field: str | None = None
    applied_at: datetime | None = None
    applied_by: UserId | None = None
    notes: str | None = None
    events: list[DomainEvent] = field(default_factory=list["DomainEvent"])

    def __post_init__(self) -> None:
        if not self.file_hash or not self.file_hash.strip():
            raise DomainError("Import batch requires a file hash for provenance")
        if not self.source_system or not self.source_system.strip():
            raise DomainError("Import batch requires a source system")
        if self.row_count < 0:
            raise DomainError("Import batch row count cannot be negative")

    @property
    def uses_file_hash_replay_key(self) -> bool:
        """True when the source has no stable id, so replay is per exact file."""
        return self.source_record_key_field is None

    def mark_applied(self, actor: UserId, *, at: datetime, accepted_count: int) -> None:
        if self.status is not ImportBatchStatus.STAGED:
            raise DomainError(f"Cannot apply a batch in status {self.status.value}")
        self.status = ImportBatchStatus.APPLIED
        self.applied_by = actor
        self.applied_at = at
        self.updated_at = at
        self.events.append(
            SessionImportBatchApplied(
                occurred_at=at,
                batch_id=self.id,
                tenant_id=self.tenant_id,
                accepted_count=accepted_count,
                actor=actor,
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
            SessionImportBatchAbandoned(
                occurred_at=at,
                batch_id=self.id,
                tenant_id=self.tenant_id,
                actor=actor,
                reason=reason,
            )
        )

    def clear_events(self) -> None:
        self.events.clear()


@dataclass
class SessionImportRowEntity:
    """One source row, its reconciliation outcome, and why.

    A row is only importable once it names a resolved practitioner and an
    explicit delivery context. Unknown context is allowed here and nowhere
    else, because a historical record may genuinely lack the evidence.
    """

    id: SessionImportRowId
    batch_id: SessionImportBatchId
    tenant_id: TenantId
    row_number: int
    source_record_key: str | None
    raw_practitioner_name: str | None
    session_date: date | None
    outcome: ImportRowOutcome
    created_at: datetime
    delivery_context: DeliveryContext = DeliveryContext.UNKNOWN
    provider_id: ProviderId | None = None
    provider_affiliation_id: ProviderAffiliationId | None = None
    imported_session_id: str | None = None
    staged_replay_key: str | None = None
    reasons: tuple[str, ...] = field(default_factory=tuple)
    # Resolved subject: who the session was for and what was delivered.
    client_id: str | None = None
    attendance: SessionAttendance | None = None
    member_id: str | None = None
    service_id: str | None = None
    # Normalised activity-log values; None where the source did not map.
    session_type: SessionType | None = None
    category: SessionCategory | None = None
    clinical_outcome: SessionClinicalStatus | None = None
    session_status: SessionStatus | None = None
    client_type: ClientType | None = None
    rate_ugx: int | None = None
    session_number: int | None = None

    def __post_init__(self) -> None:
        if self.row_number < 1:
            raise DomainError("Import row number is 1-based")
        self._validate_context()
        if self.outcome is ImportRowOutcome.ACCEPTED and self.provider_id is None:
            raise DomainError("An accepted row requires a resolved practitioner")
        if self.outcome is ImportRowOutcome.ACCEPTED and self.session_date is None:
            raise DomainError("An accepted row requires a session date")
        if self.outcome in _REVIEW_OUTCOMES and not self.reasons:
            raise DomainError("A row held for review must record why")

    def _validate_context(self) -> None:
        if self.delivery_context is DeliveryContext.ORGANISATION:
            if self.provider_affiliation_id is None:
                raise DomainError("Organisation delivery requires an affiliation")
        elif self.provider_affiliation_id is not None:
            raise DomainError(
                f"{self.delivery_context.value} delivery must not carry an affiliation"
            )

    @property
    def is_importable(self) -> bool:
        """Accepted and not already written. Both halves matter on replay."""
        return self.outcome is ImportRowOutcome.ACCEPTED and self.imported_session_id is None

    def mark_imported(self, session_id: str) -> None:
        if self.imported_session_id is not None:
            raise DomainError(
                f"Row {self.row_number} was already imported as {self.imported_session_id}"
            )
        self.imported_session_id = session_id

    @property
    def needs_review(self) -> bool:
        return self.outcome in _REVIEW_OUTCOMES

    def replay_key(self, file_hash: str) -> str:
        """The key this row claims, or defers with.

        Staging decides it, because only staging knows whether the source row
        is already accounted for elsewhere; a row that found an earlier claim
        defers instead of claiming the same key twice. `staged_replay_key`
        carries that decision. Without one the key is derived, which is what a
        row built outside staging gets: a stable source id if the source has
        one, otherwise the file and row number.
        """
        if self.staged_replay_key:
            return self.staged_replay_key
        if self.source_record_key:
            return f"key:{self.source_record_key}"
        return f"file:{file_hash}:row:{self.row_number}"
