"""Manager-as-client workflow + work-life referrals + training enrolments.

Three small aggregates that together form the "other 60% of EAP volume" —
the consultative, non-clinical interactions between Minet and employer-side
managers, plus the concierge work-life service network and the training
enrolments managers must complete to access certain referral flows.

ManagerConsult is *not* a clinical-chart entity. Even when it triggers a
formal referral that opens a Case on an employee, the consult-notes
themselves never link into that Case's chart — only the metadata. This
separation is enforced by the route guard, not by this aggregate.
"""

from dataclasses import dataclass, field
from datetime import date, datetime

from app.domain.enums import (
    ManagerConsultTopic,
    TrainingEnrolmentStatus,
    WorkLifeReferralOutcome,
    WorkLifeServiceType,
)
from app.domain.events import (
    DomainEvent,
    ManagerConsultLogged,
    ManagerConsultReferralFiled,
    TrainingEnrolmentCompleted,
    TrainingEnrolmentCreated,
    WorkLifeReferralRequested,
    WorkLifeReferralResolved,
)
from app.domain.exceptions import DomainError, InvalidStateError
from app.domain.value_objects.core import (
    CaseId,
    ClientId,
    ClinicalSubjectId,
    DocumentId,
    ManagerConsultId,
    PersonId,
    TenantId,
    TrainingEnrolmentId,
    UserId,
    WorkLifeProviderId,
    WorkLifeReferralId,
)
from app.shared.utils.datetime import utc_now


@dataclass
class ManagerConsult:
    id: ManagerConsultId
    tenant_id: TenantId
    manager_id: PersonId
    consultant_id: UserId
    topic: ManagerConsultTopic
    consulted_at: datetime
    notes: str
    created_at: datetime
    updated_at: datetime
    client_id: ClientId | None = None
    triggered_referral_case_id: CaseId | None = None
    closed_at: datetime | None = None
    events: list[DomainEvent] = field(default_factory=list[DomainEvent])

    def __post_init__(self) -> None:
        if not self.notes:
            raise DomainError("ManagerConsult requires notes")
        if self.created_at == self.updated_at and not self.events:
            self.events.append(
                ManagerConsultLogged(
                    occurred_at=self.created_at,
                    manager_consult_id=self.id,
                    manager_id=self.manager_id,
                    topic=self.topic.value,
                )
            )

    def is_closed(self) -> bool:
        return self.closed_at is not None

    def attach_referral(self, case_id: CaseId, *, now: datetime | None = None) -> None:
        if self.is_closed():
            raise InvalidStateError("Cannot attach a referral to a closed manager consult")
        now = now or utc_now()
        self.triggered_referral_case_id = case_id
        self.updated_at = now
        self.events.append(
            ManagerConsultReferralFiled(
                occurred_at=now,
                manager_consult_id=self.id,
                triggered_case_id=case_id,
            )
        )

    def close(self, *, now: datetime | None = None) -> None:
        if self.is_closed():
            return
        now = now or utc_now()
        self.closed_at = now
        self.updated_at = now


@dataclass
class WorkLifeProvider:
    id: WorkLifeProviderId
    tenant_id: TenantId
    name: str
    service_types: tuple[WorkLifeServiceType, ...]
    is_active: bool
    created_at: datetime
    updated_at: datetime
    contact_name: str | None = None
    contact_email: str | None = None
    contact_phone: str | None = None
    coverage_notes: str | None = None
    rate_card_notes: str | None = None
    last_verified_at: datetime | None = None
    deactivated_at: datetime | None = None

    def __post_init__(self) -> None:
        if not self.name:
            raise DomainError("WorkLifeProvider requires a name")
        if not self.service_types:
            raise DomainError("WorkLifeProvider must offer at least one service")

    def deactivate(self, *, now: datetime | None = None) -> None:
        if not self.is_active:
            return
        now = now or utc_now()
        self.is_active = False
        self.deactivated_at = now
        self.updated_at = now

    def reactivate(self, *, now: datetime | None = None) -> None:
        if self.is_active:
            return
        now = now or utc_now()
        self.is_active = True
        self.deactivated_at = None
        self.updated_at = now


@dataclass
class WorkLifeReferral:
    id: WorkLifeReferralId
    tenant_id: TenantId
    clinical_subject_id: ClinicalSubjectId
    service_type: WorkLifeServiceType
    requested_at: datetime
    outcome: WorkLifeReferralOutcome
    created_at: datetime
    updated_at: datetime
    referred_provider_id: WorkLifeProviderId | None = None
    case_id: CaseId | None = None
    requested_by: UserId | None = None
    resolution_notes: str | None = None
    resolved_at: datetime | None = None
    events: list[DomainEvent] = field(default_factory=list[DomainEvent])

    def __post_init__(self) -> None:
        if self.created_at == self.updated_at and not self.events:
            self.events.append(
                WorkLifeReferralRequested(
                    occurred_at=self.created_at,
                    referral_id=self.id,
                    service_type=self.service_type.value,
                )
            )

    def is_terminal(self) -> bool:
        return self.outcome in {
            WorkLifeReferralOutcome.COMPLETED,
            WorkLifeReferralOutcome.DECLINED,
            WorkLifeReferralOutcome.NO_SHOW,
        }

    def assign_provider(
        self, provider_id: WorkLifeProviderId, *, now: datetime | None = None
    ) -> None:
        if self.is_terminal():
            raise InvalidStateError("Cannot reassign provider on a terminal referral")
        self.referred_provider_id = provider_id
        self.outcome = WorkLifeReferralOutcome.ACCEPTED
        self.updated_at = now or utc_now()

    def resolve(
        self,
        *,
        outcome: WorkLifeReferralOutcome,
        notes: str | None = None,
        now: datetime | None = None,
    ) -> None:
        if outcome == WorkLifeReferralOutcome.REQUESTED:
            raise DomainError("Resolution requires a terminal outcome")
        if self.is_terminal():
            raise InvalidStateError("Referral has already been resolved")
        now = now or utc_now()
        self.outcome = outcome
        self.resolution_notes = notes
        self.resolved_at = now
        self.updated_at = now
        self.events.append(
            WorkLifeReferralResolved(
                occurred_at=now,
                referral_id=self.id,
                outcome=outcome.value,
            )
        )


@dataclass
class TrainingEnrolment:
    """Records a manager or staff member's enrolment in a training module.

    The training material itself lives in the existing ``Document`` aggregate
    (typed `TrainingMaterial`); this entity records who enrolled, when they
    completed, and when their certification expires.
    """

    id: TrainingEnrolmentId
    tenant_id: TenantId
    trainee_id: UserId
    document_id: DocumentId
    status: TrainingEnrolmentStatus
    enrolled_at: datetime
    created_at: datetime
    updated_at: datetime
    completed_at: datetime | None = None
    expires_on: date | None = None
    revoked_at: datetime | None = None
    revoked_reason: str | None = None
    events: list[DomainEvent] = field(default_factory=list[DomainEvent])

    def __post_init__(self) -> None:
        if self.created_at == self.updated_at and not self.events:
            self.events.append(
                TrainingEnrolmentCreated(
                    occurred_at=self.created_at,
                    enrolment_id=self.id,
                    trainee_id=self.trainee_id,
                    document_id=self.document_id,
                )
            )

    def mark_completed(
        self,
        *,
        expires_on: date | None = None,
        now: datetime | None = None,
    ) -> None:
        if self.status not in {
            TrainingEnrolmentStatus.ENROLLED,
            TrainingEnrolmentStatus.EXPIRED,
        }:
            raise InvalidStateError(f"Cannot complete from {self.status.value}")
        now = now or utc_now()
        self.status = TrainingEnrolmentStatus.COMPLETED
        self.completed_at = now
        self.expires_on = expires_on
        self.updated_at = now
        self.events.append(TrainingEnrolmentCompleted(occurred_at=now, enrolment_id=self.id))

    def mark_expired_if_due(self, *, today: date | None = None) -> bool:
        if self.status != TrainingEnrolmentStatus.COMPLETED:
            return False
        if self.expires_on is None:
            return False
        if self.expires_on >= (today or utc_now().date()):
            return False
        self.status = TrainingEnrolmentStatus.EXPIRED
        self.updated_at = utc_now()
        return True

    def revoke(self, *, reason: str, now: datetime | None = None) -> None:
        if not reason:
            raise DomainError("Revocation requires a reason")
        if self.status == TrainingEnrolmentStatus.REVOKED:
            return
        now = now or utc_now()
        self.status = TrainingEnrolmentStatus.REVOKED
        self.revoked_at = now
        self.revoked_reason = reason
        self.updated_at = now
