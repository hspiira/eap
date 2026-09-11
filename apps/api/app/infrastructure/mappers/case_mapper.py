"""Clinical case mapper."""

from app.core.encryption import decrypt, encrypt
from app.domain.entities.case import Case
from app.domain.enums import (
    CaseClosureReason,
    CaseStatus,
)
from app.domain.value_objects.core import (
    AuthorizationId,
    CaseId,
    ClientId,
    ClinicalSubjectId,
    PersonId,
    TenantId,
    UserId,
)
from app.infrastructure.models.case_model import CaseModel
from app.shared.utils.datetime import ensure_utc


class CaseMapper:
    @staticmethod
    def to_entity(model: CaseModel) -> Case:
        entity = Case(
            id=CaseId(model.id),
            tenant_id=TenantId(model.tenant_id),
            clinical_subject_id=ClinicalSubjectId(model.clinical_subject_id),
            client_id=ClientId(model.client_id),
            presenting_problem=model.presenting_problem,
            referral_source=model.referral_source,
            status=CaseStatus(model.status),
            opened_at=ensure_utc(model.opened_at),
            assigned_counsellor_id=PersonId(model.assigned_counsellor_id)
            if model.assigned_counsellor_id
            else None,
            authorization_id=AuthorizationId(model.authorization_id)
            if model.authorization_id
            else None,
            referred_by_user_id=UserId(model.referred_by_user_id)
            if model.referred_by_user_id
            else None,
            referral_notes=decrypt(model.referral_notes, tenant_id=model.tenant_id),
            closed_at=ensure_utc(model.closed_at) if model.closed_at else None,
            closure_reason=CaseClosureReason(model.closure_reason)
            if model.closure_reason
            else None,
            closure_summary_note_id=model.closure_summary_note_id,
            intake_screener_admin_ids=tuple(model.intake_screener_admin_ids or []),
            closure_screener_admin_ids=tuple(model.closure_screener_admin_ids or []),
            created_at=ensure_utc(model.created_at),
            updated_at=ensure_utc(model.updated_at),
        )
        entity.events.clear()
        return entity

    @staticmethod
    def to_model(entity: Case) -> CaseModel:
        return CaseModel(
            id=entity.id.value,
            tenant_id=entity.tenant_id.value,
            clinical_subject_id=entity.clinical_subject_id.value,
            client_id=entity.client_id.value,
            presenting_problem=entity.presenting_problem,
            referral_source=entity.referral_source,
            status=entity.status,
            opened_at=ensure_utc(entity.opened_at),
            assigned_counsellor_id=entity.assigned_counsellor_id.value
            if entity.assigned_counsellor_id
            else None,
            authorization_id=entity.authorization_id.value if entity.authorization_id else None,
            referred_by_user_id=entity.referred_by_user_id.value
            if entity.referred_by_user_id
            else None,
            referral_notes=encrypt(entity.referral_notes, tenant_id=entity.tenant_id.value),
            closed_at=ensure_utc(entity.closed_at) if entity.closed_at else None,
            closure_reason=entity.closure_reason,
            closure_summary_note_id=entity.closure_summary_note_id,
            intake_screener_admin_ids=list(entity.intake_screener_admin_ids),
            closure_screener_admin_ids=list(entity.closure_screener_admin_ids),
            created_at=ensure_utc(entity.created_at),
            updated_at=ensure_utc(entity.updated_at),
        )
