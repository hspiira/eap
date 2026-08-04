"""Domain events for the manager bounded context."""

from dataclasses import dataclass

from app.domain.events.base import DomainEvent
from app.domain.value_objects.core import (
    CaseId,
    ClinicalSubjectId,
    DocumentId,
    FitnessForDutyId,
    ManagerConsultId,
    OutcomeMeasureId,
    PersonId,
    ReturnToWorkPlanId,
    TrainingEnrolmentId,
    UserId,
    WorkLifeReferralId,
)


@dataclass(frozen=True)
class ManagerConsultLogged(DomainEvent):
    manager_consult_id: "ManagerConsultId"
    manager_id: PersonId
    topic: str


@dataclass(frozen=True)
class ManagerConsultReferralFiled(DomainEvent):
    manager_consult_id: "ManagerConsultId"
    triggered_case_id: "CaseId"


@dataclass(frozen=True)
class WorkLifeReferralRequested(DomainEvent):
    referral_id: "WorkLifeReferralId"
    service_type: str


@dataclass(frozen=True)
class WorkLifeReferralResolved(DomainEvent):
    referral_id: "WorkLifeReferralId"
    outcome: str


@dataclass(frozen=True)
class TrainingEnrolmentCreated(DomainEvent):
    enrolment_id: "TrainingEnrolmentId"
    trainee_id: UserId
    document_id: DocumentId


@dataclass(frozen=True)
class TrainingEnrolmentCompleted(DomainEvent):
    enrolment_id: "TrainingEnrolmentId"


@dataclass(frozen=True)
class OutcomeMeasureRecorded(DomainEvent):
    outcome_measure_id: "OutcomeMeasureId"
    case_id: "CaseId"
    instrument_code: str
    delta: float
    reliable_change_index: float
    meets_clinically_significant_change: bool


@dataclass(frozen=True)
class FitnessForDutyRequested(DomainEvent):
    fitness_for_duty_id: "FitnessForDutyId"
    clinical_subject_id: "ClinicalSubjectId"


@dataclass(frozen=True)
class FitnessForDutyResolved(DomainEvent):
    fitness_for_duty_id: "FitnessForDutyId"
    outcome: str


@dataclass(frozen=True)
class ReturnToWorkPlanActivated(DomainEvent):
    plan_id: "ReturnToWorkPlanId"


@dataclass(frozen=True)
class ReturnToWorkPlanCompleted(DomainEvent):
    plan_id: "ReturnToWorkPlanId"
