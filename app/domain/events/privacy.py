"""Domain events for the privacy bounded context."""

from dataclasses import dataclass

from app.domain.events.base import DomainEvent
from app.domain.value_objects.core import (
    ClinicalSubjectId,
    ConsentId,
    DataSharingRegisterEntryId,
    DSARRequestId,
    PersonId,
    TenantId,
)


@dataclass(frozen=True)
class DSARRequestSubmitted(DomainEvent):
    request_id: "DSARRequestId"
    tenant_id: TenantId
    subject_person_id: PersonId
    request_type: str


@dataclass(frozen=True)
class DSARRequestCompleted(DomainEvent):
    request_id: "DSARRequestId"
    request_type: str


@dataclass(frozen=True)
class DSARErasureExecuted(DomainEvent):
    """Raised when subject PII is tombstoned. Carries no PII itself by design."""

    request_id: "DSARRequestId"
    subject_person_id: PersonId
    tombstone_token: str


@dataclass(frozen=True)
class ConsentRequested(DomainEvent):
    consent_id: "ConsentId"
    subject_clinical_subject_id: "ClinicalSubjectId"
    scope: str
    purpose: str


@dataclass(frozen=True)
class ConsentGranted(DomainEvent):
    consent_id: "ConsentId"
    scope: str
    expires_on: object | None


@dataclass(frozen=True)
class ConsentRevoked(DomainEvent):
    consent_id: "ConsentId"
    reason: str


@dataclass(frozen=True)
class ConsentExpired(DomainEvent):
    consent_id: "ConsentId"


@dataclass(frozen=True)
class DataShareLogged(DomainEvent):
    entry_id: "DataSharingRegisterEntryId"
    consent_id: "ConsentId | None"
    shared_with: str
    scope: str
