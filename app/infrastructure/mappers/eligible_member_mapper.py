"""Eligible-member + clinical-subject mappers."""

from app.domain.entities.clinical_subject import ClinicalSubject
from app.domain.entities.eligible_member import EligibleMember
from app.domain.enums import EligibilityStatus, MemberRelation
from app.domain.value_objects.core import (
    ClientId,
    ClinicalSubjectId,
    EligibleMemberId,
    Email,
    TenantId,
    UserId,
)
from app.infrastructure.models.eligible_member_model import (
    ClinicalSubjectModel,
    EligibleMemberModel,
)
from app.shared.utils.datetime import ensure_utc


class EligibleMemberMapper:
    @staticmethod
    def to_entity(model: EligibleMemberModel) -> EligibleMember:
        entity = EligibleMember(
            id=EligibleMemberId(model.id),
            tenant_id=TenantId(model.tenant_id),
            client_id=ClientId(model.client_id),
            employer_member_id=model.employer_member_id,
            relation=MemberRelation(model.relation),
            status=EligibilityStatus(model.status),
            primary_employee_member_id=EligibleMemberId(model.primary_employee_member_id)
            if model.primary_employee_member_id
            else None,
            coverage_start=model.coverage_start,
            coverage_end=model.coverage_end,
            work_email=Email(model.work_email) if model.work_email else None,
            personal_email=Email(model.personal_email)
            if model.personal_email
            else None,
            display_label=model.display_label,
            last_imported_at=ensure_utc(model.last_imported_at)
            if model.last_imported_at
            else None,
            suspended_at=ensure_utc(model.suspended_at)
            if model.suspended_at
            else None,
            terminated_at=ensure_utc(model.terminated_at)
            if model.terminated_at
            else None,
            created_by=UserId(model.created_by) if model.created_by else None,
            created_at=ensure_utc(model.created_at),
            updated_at=ensure_utc(model.updated_at),
        )
        entity.events.clear()
        return entity

    @staticmethod
    def to_model(entity: EligibleMember) -> EligibleMemberModel:
        return EligibleMemberModel(
            id=entity.id.value,
            tenant_id=entity.tenant_id.value,
            client_id=entity.client_id.value,
            employer_member_id=entity.employer_member_id,
            relation=entity.relation,
            status=entity.status,
            primary_employee_member_id=(
                entity.primary_employee_member_id.value
                if entity.primary_employee_member_id
                else None
            ),
            coverage_start=entity.coverage_start,
            coverage_end=entity.coverage_end,
            work_email=entity.work_email.value if entity.work_email else None,
            personal_email=entity.personal_email.value
            if entity.personal_email
            else None,
            display_label=entity.display_label,
            last_imported_at=ensure_utc(entity.last_imported_at)
            if entity.last_imported_at
            else None,
            suspended_at=ensure_utc(entity.suspended_at)
            if entity.suspended_at
            else None,
            terminated_at=ensure_utc(entity.terminated_at)
            if entity.terminated_at
            else None,
            created_by=entity.created_by.value if entity.created_by else None,
            created_at=ensure_utc(entity.created_at),
            updated_at=ensure_utc(entity.updated_at),
        )


class ClinicalSubjectMapper:
    @staticmethod
    def to_entity(model: ClinicalSubjectModel) -> ClinicalSubject:
        entity = ClinicalSubject(
            id=ClinicalSubjectId(model.id),
            tenant_id=TenantId(model.tenant_id),
            pseudonym=model.pseudonym,
            preferred_language=model.preferred_language,
            preferred_pronouns=model.preferred_pronouns,
            preferred_contact_method=model.preferred_contact_method,
            notes_for_continuity=model.notes_for_continuity,
            is_active=model.is_active,
            deactivated_at=ensure_utc(model.deactivated_at)
            if model.deactivated_at
            else None,
            created_at=ensure_utc(model.created_at),
            updated_at=ensure_utc(model.updated_at),
        )
        entity.events.clear()
        return entity

    @staticmethod
    def to_model(entity: ClinicalSubject) -> ClinicalSubjectModel:
        return ClinicalSubjectModel(
            id=entity.id.value,
            tenant_id=entity.tenant_id.value,
            pseudonym=entity.pseudonym,
            preferred_language=entity.preferred_language,
            preferred_pronouns=entity.preferred_pronouns,
            preferred_contact_method=entity.preferred_contact_method,
            notes_for_continuity=entity.notes_for_continuity,
            is_active=entity.is_active,
            deactivated_at=ensure_utc(entity.deactivated_at)
            if entity.deactivated_at
            else None,
            created_at=ensure_utc(entity.created_at),
            updated_at=ensure_utc(entity.updated_at),
        )
