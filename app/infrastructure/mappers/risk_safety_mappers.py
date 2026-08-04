"""Risk-safety mappers."""

from app.domain.entities.caring_contact import CaringContact
from app.domain.entities.mandatory_report import MandatoryReport
from app.domain.entities.risk_assessment import RiskAssessment
from app.domain.entities.safety_plan import SafetyPlan
from app.domain.enums import (
    CaringContactChannel,
    CaringContactOutcome,
    MandatoryReportType,
    SafetyPlanStatus,
    TriageRiskLevel,
)
from app.domain.value_objects.core import (
    CaringContactId,
    CaseId,
    ClinicalSubjectId,
    CrisisContactId,
    MandatoryReportId,
    RiskAssessmentId,
    SafetyPlanId,
    TenantId,
    UserId,
)
from app.infrastructure.models.risk_safety_models import (
    CaringContactModel,
    MandatoryReportModel,
    RiskAssessmentModel,
    SafetyPlanModel,
)
from app.shared.utils.datetime import ensure_utc


class RiskAssessmentMapper:
    @staticmethod
    def to_entity(model: RiskAssessmentModel) -> RiskAssessment:
        entity = RiskAssessment(
            id=RiskAssessmentId(model.id),
            tenant_id=TenantId(model.tenant_id),
            clinical_subject_id=ClinicalSubjectId(model.clinical_subject_id),
            case_id=CaseId(model.case_id) if model.case_id else None,
            crisis_contact_id=CrisisContactId(model.crisis_contact_id)
            if model.crisis_contact_id
            else None,
            assessor_id=UserId(model.assessor_id),
            assessed_at=ensure_utc(model.assessed_at),
            risk_level=TriageRiskLevel(model.risk_level),
            imminent_harm_to_self=model.imminent_harm_to_self,
            imminent_harm_to_others=model.imminent_harm_to_others,
            child_safety_concern=model.child_safety_concern,
            vulnerable_adult_concern=model.vulnerable_adult_concern,
            requires_safety_plan=model.requires_safety_plan,
            requires_mandatory_report=model.requires_mandatory_report,
            rationale=model.rationale,
            questionnaire_response_ids=tuple(model.questionnaire_response_ids or []),
            created_at=ensure_utc(model.created_at),
            updated_at=ensure_utc(model.updated_at),
        )
        entity.events.clear()
        return entity

    @staticmethod
    def to_model(entity: RiskAssessment) -> RiskAssessmentModel:
        return RiskAssessmentModel(
            id=entity.id.value,
            tenant_id=entity.tenant_id.value,
            clinical_subject_id=entity.clinical_subject_id.value,
            case_id=entity.case_id.value if entity.case_id else None,
            crisis_contact_id=entity.crisis_contact_id.value if entity.crisis_contact_id else None,
            assessor_id=entity.assessor_id.value,
            assessed_at=ensure_utc(entity.assessed_at),
            risk_level=entity.risk_level,
            imminent_harm_to_self=entity.imminent_harm_to_self,
            imminent_harm_to_others=entity.imminent_harm_to_others,
            child_safety_concern=entity.child_safety_concern,
            vulnerable_adult_concern=entity.vulnerable_adult_concern,
            requires_safety_plan=entity.requires_safety_plan,
            requires_mandatory_report=entity.requires_mandatory_report,
            rationale=entity.rationale,
            questionnaire_response_ids=list(entity.questionnaire_response_ids),
            created_at=ensure_utc(entity.created_at),
            updated_at=ensure_utc(entity.updated_at),
        )


class SafetyPlanMapper:
    @staticmethod
    def to_entity(model: SafetyPlanModel) -> SafetyPlan:
        entity = SafetyPlan(
            id=SafetyPlanId(model.id),
            tenant_id=TenantId(model.tenant_id),
            clinical_subject_id=ClinicalSubjectId(model.clinical_subject_id),
            case_id=CaseId(model.case_id) if model.case_id else None,
            crisis_contact_id=CrisisContactId(model.crisis_contact_id)
            if model.crisis_contact_id
            else None,
            clinician_id=UserId(model.clinician_id),
            status=SafetyPlanStatus(model.status),
            warning_signs=tuple(model.warning_signs or []),
            internal_coping_strategies=tuple(model.internal_coping_strategies or []),
            social_distractions=tuple(model.social_distractions or []),
            social_contacts_for_help=tuple(model.social_contacts_for_help or []),
            professional_help_resources=tuple(model.professional_help_resources or []),
            means_restriction_plan=tuple(model.means_restriction_plan or []),
            activated_at=ensure_utc(model.activated_at) if model.activated_at else None,
            next_review_at=ensure_utc(model.next_review_at) if model.next_review_at else None,
            reviewed_at=ensure_utc(model.reviewed_at) if model.reviewed_at else None,
            reviewed_by=UserId(model.reviewed_by) if model.reviewed_by else None,
            supersedes_safety_plan_id=SafetyPlanId(model.supersedes_safety_plan_id)
            if model.supersedes_safety_plan_id
            else None,
            superseded_by=SafetyPlanId(model.superseded_by) if model.superseded_by else None,
            superseded_at=ensure_utc(model.superseded_at) if model.superseded_at else None,
            created_at=ensure_utc(model.created_at),
            updated_at=ensure_utc(model.updated_at),
        )
        entity.events.clear()
        return entity

    @staticmethod
    def to_model(entity: SafetyPlan) -> SafetyPlanModel:
        return SafetyPlanModel(
            id=entity.id.value,
            tenant_id=entity.tenant_id.value,
            clinical_subject_id=entity.clinical_subject_id.value,
            case_id=entity.case_id.value if entity.case_id else None,
            crisis_contact_id=entity.crisis_contact_id.value if entity.crisis_contact_id else None,
            clinician_id=entity.clinician_id.value,
            status=entity.status,
            warning_signs=list(entity.warning_signs),
            internal_coping_strategies=list(entity.internal_coping_strategies),
            social_distractions=list(entity.social_distractions),
            social_contacts_for_help=list(entity.social_contacts_for_help),
            professional_help_resources=list(entity.professional_help_resources),
            means_restriction_plan=list(entity.means_restriction_plan),
            activated_at=ensure_utc(entity.activated_at) if entity.activated_at else None,
            next_review_at=ensure_utc(entity.next_review_at) if entity.next_review_at else None,
            reviewed_at=ensure_utc(entity.reviewed_at) if entity.reviewed_at else None,
            reviewed_by=entity.reviewed_by.value if entity.reviewed_by else None,
            supersedes_safety_plan_id=entity.supersedes_safety_plan_id.value
            if entity.supersedes_safety_plan_id
            else None,
            superseded_by=entity.superseded_by.value if entity.superseded_by else None,
            superseded_at=ensure_utc(entity.superseded_at) if entity.superseded_at else None,
            created_at=ensure_utc(entity.created_at),
            updated_at=ensure_utc(entity.updated_at),
        )


class MandatoryReportMapper:
    @staticmethod
    def to_entity(model: MandatoryReportModel) -> MandatoryReport:
        return MandatoryReport(
            id=MandatoryReportId(model.id),
            tenant_id=TenantId(model.tenant_id),
            clinical_subject_id=ClinicalSubjectId(model.clinical_subject_id),
            risk_assessment_id=RiskAssessmentId(model.risk_assessment_id),
            case_id=CaseId(model.case_id) if model.case_id else None,
            crisis_contact_id=CrisisContactId(model.crisis_contact_id)
            if model.crisis_contact_id
            else None,
            report_type=MandatoryReportType(model.report_type),
            submitted_to=model.submitted_to,
            submitted_at=ensure_utc(model.submitted_at),
            submitted_by=UserId(model.submitted_by),
            external_reference_number=model.external_reference_number,
            contact_email=model.contact_email,
            contact_phone=model.contact_phone,
            created_at=ensure_utc(model.created_at),
        )

    @staticmethod
    def to_model(entity: MandatoryReport) -> MandatoryReportModel:
        return MandatoryReportModel(
            id=entity.id.value,
            tenant_id=entity.tenant_id.value,
            clinical_subject_id=entity.clinical_subject_id.value,
            risk_assessment_id=entity.risk_assessment_id.value,
            case_id=entity.case_id.value if entity.case_id else None,
            crisis_contact_id=entity.crisis_contact_id.value if entity.crisis_contact_id else None,
            report_type=entity.report_type,
            submitted_to=entity.submitted_to,
            submitted_at=ensure_utc(entity.submitted_at),
            submitted_by=entity.submitted_by.value,
            external_reference_number=entity.external_reference_number,
            contact_email=entity.contact_email,
            contact_phone=entity.contact_phone,
            created_at=ensure_utc(entity.created_at),
            updated_at=ensure_utc(entity.created_at),
        )


class CaringContactMapper:
    @staticmethod
    def to_entity(model: CaringContactModel) -> CaringContact:
        entity = CaringContact(
            id=CaringContactId(model.id),
            tenant_id=TenantId(model.tenant_id),
            clinical_subject_id=ClinicalSubjectId(model.clinical_subject_id),
            crisis_contact_id=CrisisContactId(model.crisis_contact_id),
            case_id=CaseId(model.case_id) if model.case_id else None,
            channel=CaringContactChannel(model.channel),
            due_at=ensure_utc(model.due_at),
            outcome=CaringContactOutcome(model.outcome),
            attempted_at=ensure_utc(model.attempted_at) if model.attempted_at else None,
            completed_at=ensure_utc(model.completed_at) if model.completed_at else None,
            handled_by=UserId(model.handled_by) if model.handled_by else None,
            notes=model.notes,
            created_at=ensure_utc(model.created_at),
            updated_at=ensure_utc(model.updated_at),
        )
        entity.events.clear()
        return entity

    @staticmethod
    def to_model(entity: CaringContact) -> CaringContactModel:
        return CaringContactModel(
            id=entity.id.value,
            tenant_id=entity.tenant_id.value,
            clinical_subject_id=entity.clinical_subject_id.value,
            crisis_contact_id=entity.crisis_contact_id.value,
            case_id=entity.case_id.value if entity.case_id else None,
            channel=entity.channel,
            due_at=ensure_utc(entity.due_at),
            outcome=entity.outcome,
            attempted_at=ensure_utc(entity.attempted_at) if entity.attempted_at else None,
            completed_at=ensure_utc(entity.completed_at) if entity.completed_at else None,
            handled_by=entity.handled_by.value if entity.handled_by else None,
            notes=entity.notes,
            created_at=ensure_utc(entity.created_at),
            updated_at=ensure_utc(entity.updated_at),
        )
