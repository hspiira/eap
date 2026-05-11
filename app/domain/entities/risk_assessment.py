"""Risk-assessment aggregate.

A composite clinical decision: the clinician's rolled-up reading of the
risk picture for one moment in time. May reference multiple underlying
``QuestionnaireResponse`` administrations (C-SSRS, PHQ-9, GAD-7, AUDIT, …)
and is the source-of-truth for downstream escalation logic:

* ``requires_safety_plan`` gates the corresponding aggregate creation.
* ``requires_mandatory_report`` gates the ``MandatoryReport`` aggregate.

Records produced inside a ``CrisisContact`` reference its ``crisis_contact_id``;
those produced inside a ``Case`` reference its ``case_id``. Both fields may be
set when an in-case assessment is triggered by a crisis call.
"""

from dataclasses import dataclass, field
from datetime import datetime

from app.domain.enums import TriageRiskLevel
from app.domain.events import DomainEvent, RiskAssessmentRecorded
from app.domain.exceptions import DomainError
from app.domain.value_objects.core import (
    CaseId,
    ClinicalSubjectId,
    CrisisContactId,
    RiskAssessmentId,
    TenantId,
    UserId,
)


@dataclass
class RiskAssessment:
    id: RiskAssessmentId
    tenant_id: TenantId
    clinical_subject_id: ClinicalSubjectId
    assessor_id: UserId
    assessed_at: datetime
    risk_level: TriageRiskLevel
    imminent_harm_to_self: bool
    imminent_harm_to_others: bool
    child_safety_concern: bool
    vulnerable_adult_concern: bool
    rationale: str
    created_at: datetime
    updated_at: datetime
    case_id: CaseId | None = None
    crisis_contact_id: CrisisContactId | None = None
    questionnaire_response_ids: tuple[str, ...] = ()
    requires_safety_plan: bool = False
    requires_mandatory_report: bool = False
    events: list[DomainEvent] = field(default_factory=list)

    def __post_init__(self) -> None:
        if not self.rationale:
            raise DomainError("RiskAssessment requires a rationale")
        if self.case_id is None and self.crisis_contact_id is None:
            raise DomainError(
                "RiskAssessment must reference at least one of case_id or crisis_contact_id"
            )
        triggers = (
            self.imminent_harm_to_self
            or self.imminent_harm_to_others
            or self.child_safety_concern
            or self.vulnerable_adult_concern
        )
        if triggers and not self.requires_mandatory_report:
            self.requires_mandatory_report = True
        if self.imminent_harm_to_self and not self.requires_safety_plan:
            self.requires_safety_plan = True
        if self.risk_level == TriageRiskLevel.CRITICAL and not self.requires_safety_plan:
            self.requires_safety_plan = True
        if self.created_at == self.updated_at and not self.events:
            self.events.append(
                RiskAssessmentRecorded(
                    occurred_at=self.created_at,
                    risk_assessment_id=self.id,
                    case_id=self.case_id,
                    crisis_contact_id=self.crisis_contact_id,
                    risk_level=self.risk_level.value,
                    requires_safety_plan=self.requires_safety_plan,
                    requires_mandatory_report=self.requires_mandatory_report,
                )
            )
