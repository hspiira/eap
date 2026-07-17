"""Release-of-Information / Consent aggregate.

Governs every PHI disclosure beyond the EAP itself: employer reports on
mandatory referrals, hand-offs to specialists, family inclusion, court orders,
research participation. Every PHI-emitting use case checks for an active
matching `Consent` and refuses without one (fail closed).

FSM: ``Pending → Active → {Expired | Revoked}``. Activation is the digital
"signature" event — recorded with an artifact reference (the actual signed
PDF lives in the existing ``Document`` aggregate). Revocation is immediate,
permanent, and reason-required.
"""

from dataclasses import dataclass, field
from datetime import date, datetime

from app.domain.enums import ConsentPurpose, ConsentScope, ConsentStatus
from app.domain.events import (
    ConsentExpired,
    ConsentGranted,
    ConsentRequested,
    ConsentRevoked,
    DomainEvent,
)
from app.domain.exceptions import DomainError, InvalidStateError
from app.domain.value_objects.core import (
    CaseId,
    ClinicalSubjectId,
    ConsentId,
    DocumentId,
    TenantId,
    UserId,
)
from app.shared.utils.datetime import utc_now


@dataclass
class Consent:
    id: ConsentId
    tenant_id: TenantId
    subject_clinical_subject_id: ClinicalSubjectId
    scope: ConsentScope
    purpose: ConsentPurpose
    disclosure_to: str
    status: ConsentStatus
    requested_at: datetime
    requested_by: UserId
    created_at: datetime
    updated_at: datetime
    case_id: CaseId | None = None
    purpose_other_detail: str | None = None
    expires_on: date | None = None
    granted_at: datetime | None = None
    granted_by_subject_reference: str | None = None
    signed_artifact_document_id: DocumentId | None = None
    revoked_at: datetime | None = None
    revoked_reason: str | None = None
    events: list[DomainEvent] = field(default_factory=list[DomainEvent])

    def __post_init__(self) -> None:
        if not self.disclosure_to:
            raise DomainError("Consent requires a disclosure_to recipient")
        if self.purpose == ConsentPurpose.OTHER and not self.purpose_other_detail:
            raise DomainError("Purpose OTHER requires a non-empty purpose_other_detail")
        if self.created_at == self.updated_at and not self.events:
            self.events.append(
                ConsentRequested(
                    occurred_at=self.created_at,
                    consent_id=self.id,
                    subject_clinical_subject_id=self.subject_clinical_subject_id,
                    scope=self.scope.value,
                    purpose=self.purpose.value,
                )
            )

    def is_active(self, *, now: datetime | None = None) -> bool:
        if self.status != ConsentStatus.ACTIVE:
            return False
        if self.expires_on is None:
            return True
        return self.expires_on >= (now or utc_now()).date()

    def grant(
        self,
        *,
        granted_by_subject_reference: str,
        signed_artifact_document_id: DocumentId | None = None,
        now: datetime | None = None,
    ) -> None:
        if not granted_by_subject_reference:
            raise DomainError("grant requires the subject's signature reference")
        if self.status != ConsentStatus.PENDING:
            raise InvalidStateError(f"Cannot grant a consent in status {self.status.value}")
        now = now or utc_now()
        self.status = ConsentStatus.ACTIVE
        self.granted_at = now
        self.granted_by_subject_reference = granted_by_subject_reference
        self.signed_artifact_document_id = signed_artifact_document_id
        self.updated_at = now
        self.events.append(
            ConsentGranted(
                occurred_at=now,
                consent_id=self.id,
                scope=self.scope.value,
                expires_on=self.expires_on,
            )
        )

    def revoke(self, *, reason: str, now: datetime | None = None) -> None:
        if not reason:
            raise DomainError("Revocation requires a reason")
        if self.status == ConsentStatus.REVOKED:
            return
        now = now or utc_now()
        self.status = ConsentStatus.REVOKED
        self.revoked_at = now
        self.revoked_reason = reason
        self.updated_at = now
        self.events.append(
            ConsentRevoked(
                occurred_at=now,
                consent_id=self.id,
                reason=reason,
            )
        )

    def expire_if_due(self, *, today: date | None = None) -> bool:
        if self.status != ConsentStatus.ACTIVE:
            return False
        if self.expires_on is None:
            return False
        if self.expires_on >= (today or utc_now().date()):
            return False
        now = utc_now()
        self.status = ConsentStatus.EXPIRED
        self.updated_at = now
        self.events.append(ConsentExpired(occurred_at=now, consent_id=self.id))
        return True
