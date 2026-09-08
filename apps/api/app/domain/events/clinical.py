"""Domain events for the clinical bounded context."""

from dataclasses import dataclass

from app.domain.events.base import DomainEvent
from app.domain.value_objects.core import (
    AuthorizationId,
    CaseId,
    ClinicalNoteId,
    ClinicalSubjectId,
    ContractId,
    EAPProgrammeId,
    PersonId,
    TenantId,
    UserId,
)


@dataclass(frozen=True)
class CaseOpened(DomainEvent):
    case_id: "CaseId"
    tenant_id: TenantId
    clinical_subject_id: "ClinicalSubjectId"
    referral_source: str
    presenting_problem: str


@dataclass(frozen=True)
class CaseAssigned(DomainEvent):
    case_id: "CaseId"
    counsellor_id: PersonId


@dataclass(frozen=True)
class CaseAdvanced(DomainEvent):
    case_id: "CaseId"
    from_status: str
    to_status: str


@dataclass(frozen=True)
class CaseClosed(DomainEvent):
    case_id: "CaseId"
    closure_reason: str


@dataclass(frozen=True)
class CaseUpdated(DomainEvent):
    """Event raised when a case's own details change outside a transition."""

    case_id: CaseId
    field: str


@dataclass(frozen=True)
class ClinicalNoteAmended(DomainEvent):
    """Event raised when a signed note is amended.

    The amendment's reason and body are on the note, not here: an audit reader
    is entitled to know a signed record was changed and by whom.
    """

    note_id: ClinicalNoteId
    amendment_id: str
    author_id: UserId


@dataclass(frozen=True)
class ClinicalNoteDraftEdited(DomainEvent):
    """Event raised when an unsigned note's body is edited."""

    note_id: ClinicalNoteId
    editor_id: UserId


@dataclass(frozen=True)
class ClinicalSubjectUpdated(DomainEvent):
    """Event raised when a subject's continuity metadata changes."""

    subject_id: ClinicalSubjectId
    field: str


@dataclass(frozen=True)
class ClinicalSubjectDeactivated(DomainEvent):
    """Event raised when a clinical subject is deactivated."""

    subject_id: ClinicalSubjectId


@dataclass(frozen=True)
class ClinicalNoteSigned(DomainEvent):
    note_id: "ClinicalNoteId"
    case_id: "CaseId"
    signer_id: UserId


@dataclass(frozen=True)
class ClinicalNoteLocked(DomainEvent):
    note_id: "ClinicalNoteId"


@dataclass(frozen=True)
class AuthorizationGranted(DomainEvent):
    authorization_id: "AuthorizationId"
    case_id: "CaseId"
    sessions_granted: int


@dataclass(frozen=True)
class AuthorizationConsumed(DomainEvent):
    authorization_id: "AuthorizationId"
    sessions_remaining: int


@dataclass(frozen=True)
class AuthorizationExtensionRequested(DomainEvent):
    authorization_id: "AuthorizationId"
    requested_additional_sessions: int


@dataclass(frozen=True)
class AuthorizationExtended(DomainEvent):
    authorization_id: "AuthorizationId"
    additional_sessions: int


@dataclass(frozen=True)
class EAPProgrammeCreated(DomainEvent):
    programme_id: "EAPProgrammeId"
    tenant_id: TenantId
    contract_id: ContractId
