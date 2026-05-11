"""Crisis contact mapper."""

from app.domain.entities.crisis_contact import CrisisContact
from app.domain.enums import (
    CrisisCallerRelation,
    CrisisContactOutcome,
    CrisisWarmHandoff,
    TriageRiskLevel,
)
from app.domain.value_objects.core import (
    CaseId,
    ClinicalSubjectId,
    CrisisContactId,
    PersonId,
    RiskAssessmentId,
    SafetyPlanId,
    TenantId,
)
from app.infrastructure.models.crisis_contact_model import CrisisContactModel
from app.shared.utils.datetime import ensure_utc


class CrisisContactMapper:
    @staticmethod
    def to_entity(model: CrisisContactModel) -> CrisisContact:
        entity = CrisisContact(
            id=CrisisContactId(model.id),
            tenant_id=TenantId(model.tenant_id),
            contacted_at=ensure_utc(model.contacted_at),
            caller_relation=CrisisCallerRelation(model.caller_relation),
            presenting_concern=model.presenting_concern,
            clinical_subject_id=ClinicalSubjectId(model.clinical_subject_id)
            if model.clinical_subject_id
            else None,
            case_id=CaseId(model.case_id) if model.case_id else None,
            counsellor_id=PersonId(model.counsellor_id)
            if model.counsellor_id
            else None,
            cssrs_administered=model.cssrs_administered,
            risk_assessment_id=RiskAssessmentId(model.risk_assessment_id)
            if model.risk_assessment_id
            else None,
            safety_plan_id=SafetyPlanId(model.safety_plan_id)
            if model.safety_plan_id
            else None,
            risk_level=TriageRiskLevel(model.risk_level)
            if model.risk_level
            else None,
            warm_handoff=CrisisWarmHandoff(model.warm_handoff),
            dispatched_at=ensure_utc(model.dispatched_at)
            if model.dispatched_at
            else None,
            outcome=CrisisContactOutcome(model.outcome)
            if model.outcome
            else None,
            resolved_at=ensure_utc(model.resolved_at)
            if model.resolved_at
            else None,
            transcript_summary=model.transcript_summary,
            created_at=ensure_utc(model.created_at),
            updated_at=ensure_utc(model.updated_at),
        )
        entity.events.clear()
        return entity

    @staticmethod
    def to_model(entity: CrisisContact) -> CrisisContactModel:
        return CrisisContactModel(
            id=entity.id.value,
            tenant_id=entity.tenant_id.value,
            contacted_at=ensure_utc(entity.contacted_at),
            caller_relation=entity.caller_relation,
            presenting_concern=entity.presenting_concern,
            clinical_subject_id=entity.clinical_subject_id.value
            if entity.clinical_subject_id
            else None,
            case_id=entity.case_id.value if entity.case_id else None,
            counsellor_id=entity.counsellor_id.value
            if entity.counsellor_id
            else None,
            cssrs_administered=entity.cssrs_administered,
            risk_assessment_id=entity.risk_assessment_id.value
            if entity.risk_assessment_id
            else None,
            safety_plan_id=entity.safety_plan_id.value
            if entity.safety_plan_id
            else None,
            risk_level=entity.risk_level,
            warm_handoff=entity.warm_handoff,
            dispatched_at=ensure_utc(entity.dispatched_at)
            if entity.dispatched_at
            else None,
            outcome=entity.outcome,
            resolved_at=ensure_utc(entity.resolved_at)
            if entity.resolved_at
            else None,
            transcript_summary=entity.transcript_summary,
            created_at=ensure_utc(entity.created_at),
            updated_at=ensure_utc(entity.updated_at),
        )
