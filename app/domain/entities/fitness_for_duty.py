"""Fitness-for-duty + return-to-work plan aggregates.

A Fitness-for-Duty assessment is a job-specific opinion delivered back to the
employer as a non-clinical result (Fit / Fit-with-Restrictions / Not-Fit plus
accommodation recommendations). Underlying clinical detail is **never**
disclosed via this aggregate — the disclosure scope is hard-wired to the four
result states + accommodation list.

A ReturnToWorkPlan is the operational schedule the employer + employee follow
to bring the employee back. Composes a list of phased ``Accommodation``s and
employer/clinician sign-offs.
"""

from dataclasses import dataclass, field
from datetime import date, datetime

from app.domain.enums import (
    FitnessForDutyOutcome,
    ReturnToWorkPlanStatus,
)
from app.domain.events import (
    DomainEvent,
    FitnessForDutyRequested,
    FitnessForDutyResolved,
    ReturnToWorkPlanActivated,
    ReturnToWorkPlanCompleted,
)
from app.domain.exceptions import DomainError, InvalidStateError
from app.domain.value_objects.core import (
    CaseId,
    ClientId,
    ClinicalSubjectId,
    FitnessForDutyId,
    ReturnToWorkPlanId,
    TenantId,
    UserId,
)
from app.shared.utils.datetime import utc_now


@dataclass
class FitnessForDuty:
    id: FitnessForDutyId
    tenant_id: TenantId
    clinical_subject_id: ClinicalSubjectId
    client_id: ClientId
    requested_at: datetime
    requested_by: UserId
    business_necessity_rationale: str
    job_role_summary: str
    outcome: FitnessForDutyOutcome
    created_at: datetime
    updated_at: datetime
    case_id: CaseId | None = None
    assessed_at: datetime | None = None
    assessor_id: UserId | None = None
    accommodation_recommendations: tuple[str, ...] = ()
    employer_report_at: datetime | None = None
    events: list[DomainEvent] = field(default_factory=list[DomainEvent])

    def __post_init__(self) -> None:
        if not self.business_necessity_rationale:
            raise DomainError("FitnessForDuty requires a business-necessity rationale")
        if not self.job_role_summary:
            raise DomainError("FitnessForDuty requires a job_role_summary")
        if self.created_at == self.updated_at and not self.events:
            self.events.append(
                FitnessForDutyRequested(
                    occurred_at=self.created_at,
                    fitness_for_duty_id=self.id,
                    clinical_subject_id=self.clinical_subject_id,
                )
            )

    def is_resolved(self) -> bool:
        return self.outcome != FitnessForDutyOutcome.PENDING

    def record_outcome(
        self,
        *,
        outcome: FitnessForDutyOutcome,
        assessor_id: UserId,
        accommodation_recommendations: tuple[str, ...] = (),
        now: datetime | None = None,
    ) -> None:
        if outcome == FitnessForDutyOutcome.PENDING:
            raise DomainError("record_outcome requires a terminal outcome")
        if self.is_resolved():
            raise InvalidStateError("FitnessForDuty already resolved")
        if (
            outcome == FitnessForDutyOutcome.FIT_WITH_RESTRICTIONS
            and not accommodation_recommendations
        ):
            raise DomainError("FitWithRestrictions requires accommodation_recommendations")
        now = now or utc_now()
        self.outcome = outcome
        self.assessor_id = assessor_id
        self.accommodation_recommendations = accommodation_recommendations
        self.assessed_at = now
        self.updated_at = now
        self.events.append(
            FitnessForDutyResolved(
                occurred_at=now,
                fitness_for_duty_id=self.id,
                outcome=outcome.value,
            )
        )

    def mark_employer_reported(self, *, now: datetime | None = None) -> None:
        if not self.is_resolved():
            raise InvalidStateError(
                "Cannot mark employer-reported before the assessment is resolved"
            )
        self.employer_report_at = now or utc_now()
        self.updated_at = self.employer_report_at


@dataclass(frozen=True)
class Accommodation:
    description: str
    starts_on: date
    ends_on: date | None = None

    def __post_init__(self) -> None:
        if not self.description:
            raise DomainError("Accommodation requires a description")
        if self.ends_on is not None and self.ends_on < self.starts_on:
            raise DomainError("Accommodation ends_on cannot precede starts_on")


@dataclass
class ReturnToWorkPlan:
    id: ReturnToWorkPlanId
    tenant_id: TenantId
    clinical_subject_id: ClinicalSubjectId
    client_id: ClientId
    starts_on: date
    status: ReturnToWorkPlanStatus
    accommodations: tuple[Accommodation, ...]
    created_at: datetime
    updated_at: datetime
    case_id: CaseId | None = None
    fitness_for_duty_id: FitnessForDutyId | None = None
    ends_on: date | None = None
    employer_signoff_user_id: UserId | None = None
    clinician_signoff_user_id: UserId | None = None
    activated_at: datetime | None = None
    completed_at: datetime | None = None
    cancelled_at: datetime | None = None
    cancellation_reason: str | None = None
    review_at: date | None = None
    events: list[DomainEvent] = field(default_factory=list[DomainEvent])

    def __post_init__(self) -> None:
        if not self.accommodations:
            raise DomainError("ReturnToWorkPlan requires at least one accommodation")
        if self.ends_on is not None and self.ends_on < self.starts_on:
            raise DomainError("ends_on cannot precede starts_on")

    def is_terminal(self) -> bool:
        return self.status in {
            ReturnToWorkPlanStatus.COMPLETED,
            ReturnToWorkPlanStatus.CANCELLED,
        }

    def activate(
        self,
        *,
        employer_signoff_user_id: UserId,
        clinician_signoff_user_id: UserId,
        now: datetime | None = None,
    ) -> None:
        if self.status != ReturnToWorkPlanStatus.DRAFT:
            raise InvalidStateError(f"Cannot activate a {self.status.value} plan")
        if employer_signoff_user_id == clinician_signoff_user_id:
            raise DomainError("Employer and clinician sign-off must come from different users")
        now = now or utc_now()
        self.status = ReturnToWorkPlanStatus.ACTIVE
        self.activated_at = now
        self.employer_signoff_user_id = employer_signoff_user_id
        self.clinician_signoff_user_id = clinician_signoff_user_id
        self.updated_at = now
        self.events.append(ReturnToWorkPlanActivated(occurred_at=now, plan_id=self.id))

    def complete(self, *, now: datetime | None = None) -> None:
        if self.status != ReturnToWorkPlanStatus.ACTIVE:
            raise InvalidStateError(f"Cannot complete a {self.status.value} plan")
        now = now or utc_now()
        self.status = ReturnToWorkPlanStatus.COMPLETED
        self.completed_at = now
        self.updated_at = now
        self.events.append(ReturnToWorkPlanCompleted(occurred_at=now, plan_id=self.id))

    def cancel(self, *, reason: str, now: datetime | None = None) -> None:
        if not reason:
            raise DomainError("Cancellation requires a reason")
        if self.is_terminal():
            raise InvalidStateError(f"Cannot cancel a {self.status.value} plan")
        now = now or utc_now()
        self.status = ReturnToWorkPlanStatus.CANCELLED
        self.cancelled_at = now
        self.cancellation_reason = reason
        self.updated_at = now
