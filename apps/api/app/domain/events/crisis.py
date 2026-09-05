"""Domain events for the crisis bounded context."""

from dataclasses import dataclass
from datetime import datetime

from app.domain.enums import CriticalIncidentPhase, CriticalIncidentSeverity
from app.domain.events.base import DomainEvent
from app.domain.value_objects.core import (
    CaringContactId,
    CaseId,
    ClinicalSubjectId,
    CrisisContactId,
    CriticalIncidentId,
    MandatoryReportId,
    OutreachRecordId,
    PersonId,
    RiskAssessmentId,
    SafetyPlanId,
    TenantId,
    UserId,
)


@dataclass(frozen=True)
class CriticalIncidentLogged(DomainEvent):
    """Raised when a critical incident is first logged."""

    incident_id: CriticalIncidentId
    severity: CriticalIncidentSeverity
    affected_population_size: int


@dataclass(frozen=True)
class CriticalIncidentPhaseRecorded(DomainEvent):
    """Raised when a CISM phase entry is added to the response timeline."""

    incident_id: CriticalIncidentId
    phase: CriticalIncidentPhase


@dataclass(frozen=True)
class CriticalIncidentClosed(DomainEvent):
    """Raised when an incident response is closed and the after-action is final."""

    incident_id: CriticalIncidentId


@dataclass(frozen=True)
class CrisisFlagRaised(DomainEvent):
    """Raised when triage detects acute risk (e.g. PHQ-9 item-9 > 0).

    Subscribed by a notify consumer that pages the on-call supervisor.
    """

    outreach_id: "OutreachRecordId"
    person_id: PersonId
    risk_level: str
    reason: str


@dataclass(frozen=True)
class CrisisContactLogged(DomainEvent):
    crisis_contact_id: "CrisisContactId"
    tenant_id: TenantId


@dataclass(frozen=True)
class CrisisContactClosed(DomainEvent):
    crisis_contact_id: "CrisisContactId"
    outcome: str


@dataclass(frozen=True)
class RiskAssessmentRecorded(DomainEvent):
    risk_assessment_id: "RiskAssessmentId"
    case_id: "CaseId | None"
    crisis_contact_id: "CrisisContactId | None"
    risk_level: str
    requires_safety_plan: bool
    requires_mandatory_report: bool


@dataclass(frozen=True)
class SafetyPlanCreated(DomainEvent):
    safety_plan_id: "SafetyPlanId"
    clinical_subject_id: "ClinicalSubjectId"


@dataclass(frozen=True)
class SafetyPlanActivated(DomainEvent):
    safety_plan_id: "SafetyPlanId"


@dataclass(frozen=True)
class SafetyPlanReviewed(DomainEvent):
    safety_plan_id: "SafetyPlanId"
    reviewer_id: UserId


@dataclass(frozen=True)
class SafetyPlanSuperseded(DomainEvent):
    superseded_safety_plan_id: "SafetyPlanId"
    successor_safety_plan_id: "SafetyPlanId"


@dataclass(frozen=True)
class MandatoryReportSubmitted(DomainEvent):
    mandatory_report_id: "MandatoryReportId"
    report_type: str
    submitted_to: str


@dataclass(frozen=True)
class CaringContactScheduled(DomainEvent):
    caring_contact_id: "CaringContactId"
    due_at: datetime


@dataclass(frozen=True)
class CaringContactCompleted(DomainEvent):
    caring_contact_id: "CaringContactId"
    outcome: str
