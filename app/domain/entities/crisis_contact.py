"""Crisis contact aggregate.

Captures every 24/7 hotline interaction independently of a Case. A
``CrisisContact`` may end up creating a Case (`case_id` set when the
clinician opens one) or stay standalone — either way the contact is retained
per retention policy. The aggregate's lifecycle is `Open → Resolved`; resolved
contacts can still gain follow-up linkage but cannot be mutated.
"""

from dataclasses import dataclass, field
from datetime import datetime

from app.domain.enums import (
    CrisisCallerRelation,
    CrisisContactOutcome,
    CrisisWarmHandoff,
    TriageRiskLevel,
)
from app.domain.events import (
    CrisisContactClosed,
    CrisisContactLogged,
    DomainEvent,
)
from app.domain.exceptions import DomainError, InvalidStateError
from app.domain.value_objects.core import (
    CaseId,
    ClinicalSubjectId,
    CrisisContactId,
    PersonId,
    RiskAssessmentId,
    SafetyPlanId,
    TenantId,
)
from app.shared.utils.datetime import utc_now


@dataclass
class CrisisContact:
    id: CrisisContactId
    tenant_id: TenantId
    contacted_at: datetime
    caller_relation: CrisisCallerRelation
    presenting_concern: str
    created_at: datetime
    updated_at: datetime
    clinical_subject_id: ClinicalSubjectId | None = None
    case_id: CaseId | None = None
    counsellor_id: PersonId | None = None
    cssrs_administered: bool = False
    risk_assessment_id: RiskAssessmentId | None = None
    safety_plan_id: SafetyPlanId | None = None
    risk_level: TriageRiskLevel | None = None
    warm_handoff: CrisisWarmHandoff = CrisisWarmHandoff.NONE
    dispatched_at: datetime | None = None
    outcome: CrisisContactOutcome | None = None
    resolved_at: datetime | None = None
    transcript_summary: str | None = None
    events: list[DomainEvent] = field(default_factory=list[DomainEvent])

    def __post_init__(self) -> None:
        if not self.presenting_concern:
            raise DomainError("presenting_concern is required")
        if self.created_at == self.updated_at and not self.events:
            self.events.append(
                CrisisContactLogged(
                    occurred_at=self.created_at,
                    crisis_contact_id=self.id,
                    tenant_id=self.tenant_id,
                )
            )

    def is_resolved(self) -> bool:
        return self.outcome is not None

    def attach_clinical_subject(
        self, subject_id: ClinicalSubjectId, *, now: datetime | None = None
    ) -> None:
        if self.is_resolved():
            raise InvalidStateError("Cannot mutate a resolved crisis contact")
        self.clinical_subject_id = subject_id
        self.updated_at = now or utc_now()

    def attach_case(self, case_id: CaseId, *, now: datetime | None = None) -> None:
        self.case_id = case_id
        self.updated_at = now or utc_now()

    def record_assessment(
        self,
        *,
        risk_assessment_id: RiskAssessmentId,
        risk_level: TriageRiskLevel,
        cssrs_administered: bool = True,
        now: datetime | None = None,
    ) -> None:
        if self.is_resolved():
            raise InvalidStateError("Cannot record assessment on a resolved crisis contact")
        self.risk_assessment_id = risk_assessment_id
        self.risk_level = risk_level
        self.cssrs_administered = cssrs_administered or self.cssrs_administered
        self.updated_at = now or utc_now()

    def attach_safety_plan(
        self, safety_plan_id: SafetyPlanId, *, now: datetime | None = None
    ) -> None:
        self.safety_plan_id = safety_plan_id
        self.updated_at = now or utc_now()

    def record_warm_handoff(
        self,
        *,
        destination: CrisisWarmHandoff,
        now: datetime | None = None,
    ) -> None:
        if destination == CrisisWarmHandoff.NONE:
            raise DomainError("Use record_warm_handoff for actual handoffs only")
        if self.is_resolved():
            raise InvalidStateError("Cannot record handoff on a resolved crisis contact")
        now = now or utc_now()
        self.warm_handoff = destination
        self.dispatched_at = now
        self.updated_at = now

    def resolve(
        self,
        *,
        outcome: CrisisContactOutcome,
        transcript_summary: str | None = None,
        now: datetime | None = None,
    ) -> None:
        if self.is_resolved():
            raise InvalidStateError("Crisis contact is already resolved")
        now = now or utc_now()
        self.outcome = outcome
        self.resolved_at = now
        if transcript_summary is not None:
            self.transcript_summary = transcript_summary
        self.updated_at = now
        self.events.append(
            CrisisContactClosed(
                occurred_at=now,
                crisis_contact_id=self.id,
                outcome=outcome.value,
            )
        )
