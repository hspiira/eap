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
