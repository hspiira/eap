"""Outcomes mappers."""

from datetime import date

from app.domain.entities.fitness_for_duty import (
    Accommodation,
    FitnessForDuty,
    ReturnToWorkPlan,
)
from app.domain.entities.outcome_measure import OutcomeMeasure
from app.domain.enums import (
    FitnessForDutyOutcome,
    ReturnToWorkPlanStatus,
    TriageInstrumentCode,
)
from app.domain.value_objects.core import (
    CaseId,
    ClientId,
    ClinicalSubjectId,
    FitnessForDutyId,
    OutcomeMeasureId,
    ReturnToWorkPlanId,
    TenantId,
    UserId,
)
from app.infrastructure.models.outcomes_models import (
    FitnessForDutyModel,
    OutcomeMeasureModel,
    ReturnToWorkPlanModel,
)
from app.shared.utils.datetime import ensure_utc


def _accommodation_from_dict(raw: dict) -> Accommodation:
    return Accommodation(
        description=raw["description"],
        starts_on=date.fromisoformat(raw["starts_on"]),
        ends_on=date.fromisoformat(raw["ends_on"]) if raw.get("ends_on") else None,
    )


def _accommodation_to_dict(a: Accommodation) -> dict:
    return {
        "description": a.description,
        "starts_on": a.starts_on.isoformat(),
        "ends_on": a.ends_on.isoformat() if a.ends_on else None,
    }


class OutcomeMeasureMapper:
    @staticmethod
    def to_entity(model: OutcomeMeasureModel) -> OutcomeMeasure:
        entity = OutcomeMeasure(
            id=OutcomeMeasureId(model.id),
            tenant_id=TenantId(model.tenant_id),
            case_id=CaseId(model.case_id),
            clinical_subject_id=ClinicalSubjectId(model.clinical_subject_id),
            instrument_code=TriageInstrumentCode(model.instrument_code),
            intake_response_id=model.intake_response_id,
            closure_response_id=model.closure_response_id,
            pre_score=model.pre_score,
            post_score=model.post_score,
            delta=model.delta,
            reliable_change_index=model.reliable_change_index,
            meets_clinically_significant_change=model.meets_clinically_significant_change,
            recorded_at=ensure_utc(model.recorded_at),
            created_at=ensure_utc(model.created_at),
            updated_at=ensure_utc(model.updated_at),
        )
        entity.events.clear()
        return entity

    @staticmethod
    def to_model(entity: OutcomeMeasure) -> OutcomeMeasureModel:
        return OutcomeMeasureModel(
            id=entity.id.value,
            tenant_id=entity.tenant_id.value,
            case_id=entity.case_id.value,
            clinical_subject_id=entity.clinical_subject_id.value,
            instrument_code=entity.instrument_code,
            intake_response_id=entity.intake_response_id,
            closure_response_id=entity.closure_response_id,
            pre_score=entity.pre_score,
            post_score=entity.post_score,
            delta=entity.delta,
            reliable_change_index=entity.reliable_change_index,
            meets_clinically_significant_change=entity.meets_clinically_significant_change,
            recorded_at=ensure_utc(entity.recorded_at),
            created_at=ensure_utc(entity.created_at),
            updated_at=ensure_utc(entity.updated_at),
        )


class FitnessForDutyMapper:
    @staticmethod
    def to_entity(model: FitnessForDutyModel) -> FitnessForDuty:
        entity = FitnessForDuty(
            id=FitnessForDutyId(model.id),
            tenant_id=TenantId(model.tenant_id),
            clinical_subject_id=ClinicalSubjectId(model.clinical_subject_id),
            client_id=ClientId(model.client_id),
            case_id=CaseId(model.case_id) if model.case_id else None,
            requested_at=ensure_utc(model.requested_at),
            requested_by=UserId(model.requested_by),
            business_necessity_rationale=model.business_necessity_rationale,
            job_role_summary=model.job_role_summary,
            outcome=FitnessForDutyOutcome(model.outcome),
            assessed_at=ensure_utc(model.assessed_at) if model.assessed_at else None,
            assessor_id=UserId(model.assessor_id) if model.assessor_id else None,
            accommodation_recommendations=tuple(model.accommodation_recommendations or []),
            employer_report_at=ensure_utc(model.employer_report_at)
            if model.employer_report_at
            else None,
            created_at=ensure_utc(model.created_at),
            updated_at=ensure_utc(model.updated_at),
        )
        entity.events.clear()
        return entity

    @staticmethod
    def to_model(entity: FitnessForDuty) -> FitnessForDutyModel:
        return FitnessForDutyModel(
            id=entity.id.value,
            tenant_id=entity.tenant_id.value,
            clinical_subject_id=entity.clinical_subject_id.value,
            client_id=entity.client_id.value,
            case_id=entity.case_id.value if entity.case_id else None,
            requested_at=ensure_utc(entity.requested_at),
            requested_by=entity.requested_by.value,
            business_necessity_rationale=entity.business_necessity_rationale,
            job_role_summary=entity.job_role_summary,
            outcome=entity.outcome,
            assessed_at=ensure_utc(entity.assessed_at) if entity.assessed_at else None,
            assessor_id=entity.assessor_id.value if entity.assessor_id else None,
            accommodation_recommendations=list(entity.accommodation_recommendations),
            employer_report_at=ensure_utc(entity.employer_report_at)
            if entity.employer_report_at
            else None,
            created_at=ensure_utc(entity.created_at),
            updated_at=ensure_utc(entity.updated_at),
        )


class ReturnToWorkPlanMapper:
    @staticmethod
    def to_entity(model: ReturnToWorkPlanModel) -> ReturnToWorkPlan:
        entity = ReturnToWorkPlan(
            id=ReturnToWorkPlanId(model.id),
            tenant_id=TenantId(model.tenant_id),
            clinical_subject_id=ClinicalSubjectId(model.clinical_subject_id),
            client_id=ClientId(model.client_id),
            case_id=CaseId(model.case_id) if model.case_id else None,
            fitness_for_duty_id=FitnessForDutyId(model.fitness_for_duty_id)
            if model.fitness_for_duty_id
            else None,
            starts_on=model.starts_on,
            ends_on=model.ends_on,
            status=ReturnToWorkPlanStatus(model.status),
            accommodations=tuple(_accommodation_from_dict(a) for a in (model.accommodations or [])),
            employer_signoff_user_id=UserId(model.employer_signoff_user_id)
            if model.employer_signoff_user_id
            else None,
            clinician_signoff_user_id=UserId(model.clinician_signoff_user_id)
            if model.clinician_signoff_user_id
            else None,
            activated_at=ensure_utc(model.activated_at) if model.activated_at else None,
            completed_at=ensure_utc(model.completed_at) if model.completed_at else None,
            cancelled_at=ensure_utc(model.cancelled_at) if model.cancelled_at else None,
            cancellation_reason=model.cancellation_reason,
            review_at=model.review_at,
            created_at=ensure_utc(model.created_at),
            updated_at=ensure_utc(model.updated_at),
        )
        entity.events.clear()
        return entity

    @staticmethod
    def to_model(entity: ReturnToWorkPlan) -> ReturnToWorkPlanModel:
        return ReturnToWorkPlanModel(
            id=entity.id.value,
            tenant_id=entity.tenant_id.value,
            clinical_subject_id=entity.clinical_subject_id.value,
            client_id=entity.client_id.value,
            case_id=entity.case_id.value if entity.case_id else None,
            fitness_for_duty_id=entity.fitness_for_duty_id.value
            if entity.fitness_for_duty_id
            else None,
            starts_on=entity.starts_on,
            ends_on=entity.ends_on,
            status=entity.status,
            accommodations=[_accommodation_to_dict(a) for a in entity.accommodations],
            employer_signoff_user_id=entity.employer_signoff_user_id.value
            if entity.employer_signoff_user_id
            else None,
            clinician_signoff_user_id=entity.clinician_signoff_user_id.value
            if entity.clinician_signoff_user_id
            else None,
            activated_at=ensure_utc(entity.activated_at) if entity.activated_at else None,
            completed_at=ensure_utc(entity.completed_at) if entity.completed_at else None,
            cancelled_at=ensure_utc(entity.cancelled_at) if entity.cancelled_at else None,
            cancellation_reason=entity.cancellation_reason,
            review_at=entity.review_at,
            created_at=ensure_utc(entity.created_at),
            updated_at=ensure_utc(entity.updated_at),
        )
