"""Clinical note aggregate.

Append-only, signed-and-locked. The original body text is never overwritten:
edits made before signing replace ``body``; edits requested after signing land
in the ``amendments`` collection alongside the original. Signing transitions
the note from DRAFT → SIGNED, and a configurable lock window after signature
moves it to LOCKED — after which only amendments are accepted.
"""

from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Any

from app.domain.enums import ClinicalNoteType
from app.domain.events import (
    ClinicalNoteLocked,
    ClinicalNoteSigned,
    DomainEvent,
)
from app.domain.exceptions import DomainError, InvalidStateError
from app.domain.value_objects.clinical_note_body import (
    DAPBody,
    NarrativeBody,
    SOAPBody,
)
from app.domain.value_objects.core import (
    CaseId,
    ClinicalNoteId,
    ClinicalSubjectId,
    NoteAmendmentId,
    SessionId,
    TenantId,
    UserId,
)
from app.shared.utils.datetime import utc_now


DEFAULT_LOCK_WINDOW = timedelta(days=7)


@dataclass(frozen=True)
class NoteAmendment:
    id: NoteAmendmentId
    author_id: UserId
    body: dict[str, Any]
    reason: str
    created_at: datetime

    def __post_init__(self) -> None:
        if not self.body:
            raise DomainError("Amendment body cannot be empty")
        if not self.reason:
            raise DomainError("Amendment reason cannot be empty")


@dataclass
class ClinicalNote:
    id: ClinicalNoteId
    tenant_id: TenantId
    case_id: CaseId
    clinical_subject_id: ClinicalSubjectId
    note_type: ClinicalNoteType
    body: dict[str, Any]
    author_id: UserId
    created_at: datetime
    updated_at: datetime
    session_id: SessionId | None = None
    signed_at: datetime | None = None
    signed_by: UserId | None = None
    locked_at: datetime | None = None
    lock_window: timedelta = DEFAULT_LOCK_WINDOW
    amendments: tuple[NoteAmendment, ...] = ()
    events: list[DomainEvent] = field(default_factory=list)

    def __post_init__(self) -> None:
        if not self.body:
            raise DomainError("Clinical note requires a body")

    @classmethod
    def from_dap(cls, *, body: DAPBody, **kwargs: Any) -> "ClinicalNote":
        return cls(note_type=ClinicalNoteType.DAP, body=body.as_dict(), **kwargs)

    @classmethod
    def from_soap(cls, *, body: SOAPBody, **kwargs: Any) -> "ClinicalNote":
        return cls(note_type=ClinicalNoteType.SOAP, body=body.as_dict(), **kwargs)

    @classmethod
    def from_narrative(
        cls,
        *,
        body: NarrativeBody,
        note_type: ClinicalNoteType,
        **kwargs: Any,
    ) -> "ClinicalNote":
        if note_type in {ClinicalNoteType.DAP, ClinicalNoteType.SOAP}:
            raise DomainError(
                "Narrative bodies can only be used with non-structured note types"
            )
        return cls(note_type=note_type, body=body.as_dict(), **kwargs)

    def is_signed(self) -> bool:
        return self.signed_at is not None

    def is_locked(self) -> bool:
        return self.locked_at is not None

    def update_body(self, *, new_body: dict[str, Any], editor_id: UserId) -> None:
        if self.is_signed():
            raise InvalidStateError(
                "Signed notes cannot be re-edited; use amend() instead"
            )
        if not new_body:
            raise DomainError("new_body cannot be empty")
        if editor_id != self.author_id:
            raise DomainError("Only the author can edit the draft body")
        self.body = dict(new_body)
        self.updated_at = utc_now()

    def sign(self, *, signer_id: UserId, now: datetime | None = None) -> None:
        if self.is_signed():
            raise InvalidStateError("Note is already signed")
        if signer_id != self.author_id:
            raise DomainError("Only the author may sign their own note")
        now = now or utc_now()
        self.signed_at = now
        self.signed_by = signer_id
        self.updated_at = now
        self.events.append(
            ClinicalNoteSigned(
                occurred_at=now,
                note_id=self.id,
                case_id=self.case_id,
                signer_id=signer_id,
            )
        )

    def lock_if_window_passed(self, *, now: datetime | None = None) -> bool:
        if self.is_locked():
            return False
        if not self.is_signed():
            return False
        now = now or utc_now()
        signed_at = self.signed_at
        assert signed_at is not None
        if now - signed_at < self.lock_window:
            return False
        self.locked_at = now
        self.updated_at = now
        self.events.append(
            ClinicalNoteLocked(occurred_at=now, note_id=self.id)
        )
        return True

    def amend(
        self,
        *,
        amendment_id: NoteAmendmentId,
        author_id: UserId,
        body: dict[str, Any],
        reason: str,
        now: datetime | None = None,
    ) -> NoteAmendment:
        if not self.is_signed():
            raise InvalidStateError(
                "Amendments only apply after the note is signed; edit the draft instead"
            )
        now = now or utc_now()
        amendment = NoteAmendment(
            id=amendment_id,
            author_id=author_id,
            body=dict(body),
            reason=reason,
            created_at=now,
        )
        self.amendments = (*self.amendments, amendment)
        self.updated_at = now
        return amendment
