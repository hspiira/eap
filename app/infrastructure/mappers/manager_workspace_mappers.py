"""Manager-workspace mappers."""

from app.domain.entities.manager_workspace import (
    ManagerConsult,
    TrainingEnrolment,
    WorkLifeProvider,
    WorkLifeReferral,
)
from app.domain.enums import (
    ManagerConsultTopic,
    TrainingEnrolmentStatus,
    WorkLifeReferralOutcome,
    WorkLifeServiceType,
)
from app.domain.value_objects.core import (
    CaseId,
    ClientId,
    ClinicalSubjectId,
    DocumentId,
    ManagerConsultId,
    PersonId,
    TenantId,
    TrainingEnrolmentId,
    UserId,
    WorkLifeProviderId,
    WorkLifeReferralId,
)
from app.infrastructure.models.manager_workspace_models import (
    ManagerConsultModel,
    TrainingEnrolmentModel,
    WorkLifeProviderModel,
    WorkLifeReferralModel,
)
from app.shared.utils.datetime import ensure_utc


class ManagerConsultMapper:
    @staticmethod
    def to_entity(model: ManagerConsultModel) -> ManagerConsult:
        entity = ManagerConsult(
            id=ManagerConsultId(model.id),
            tenant_id=TenantId(model.tenant_id),
            manager_id=PersonId(model.manager_id),
            consultant_id=UserId(model.consultant_id),
            topic=ManagerConsultTopic(model.topic),
            consulted_at=ensure_utc(model.consulted_at),
            notes=model.notes,
            client_id=ClientId(model.client_id) if model.client_id else None,
            triggered_referral_case_id=CaseId(model.triggered_referral_case_id)
            if model.triggered_referral_case_id
            else None,
            closed_at=ensure_utc(model.closed_at) if model.closed_at else None,
            created_at=ensure_utc(model.created_at),
            updated_at=ensure_utc(model.updated_at),
        )
        entity.events.clear()
        return entity

    @staticmethod
    def to_model(entity: ManagerConsult) -> ManagerConsultModel:
        return ManagerConsultModel(
            id=entity.id.value,
            tenant_id=entity.tenant_id.value,
            manager_id=entity.manager_id.value,
            consultant_id=entity.consultant_id.value,
            topic=entity.topic,
            consulted_at=ensure_utc(entity.consulted_at),
            notes=entity.notes,
            client_id=entity.client_id.value if entity.client_id else None,
            triggered_referral_case_id=entity.triggered_referral_case_id.value
            if entity.triggered_referral_case_id
            else None,
            closed_at=ensure_utc(entity.closed_at) if entity.closed_at else None,
            created_at=ensure_utc(entity.created_at),
            updated_at=ensure_utc(entity.updated_at),
        )


class WorkLifeProviderMapper:
    @staticmethod
    def to_entity(model: WorkLifeProviderModel) -> WorkLifeProvider:
        return WorkLifeProvider(
            id=WorkLifeProviderId(model.id),
            tenant_id=TenantId(model.tenant_id),
            name=model.name,
            service_types=tuple(
                WorkLifeServiceType(s) for s in (model.service_types or [])
            ),
            is_active=model.is_active,
            contact_name=model.contact_name,
            contact_email=model.contact_email,
            contact_phone=model.contact_phone,
            coverage_notes=model.coverage_notes,
            rate_card_notes=model.rate_card_notes,
            last_verified_at=ensure_utc(model.last_verified_at)
            if model.last_verified_at
            else None,
            deactivated_at=ensure_utc(model.deactivated_at)
            if model.deactivated_at
            else None,
            created_at=ensure_utc(model.created_at),
            updated_at=ensure_utc(model.updated_at),
        )

    @staticmethod
    def to_model(entity: WorkLifeProvider) -> WorkLifeProviderModel:
        return WorkLifeProviderModel(
            id=entity.id.value,
            tenant_id=entity.tenant_id.value,
            name=entity.name,
            service_types=[s.value for s in entity.service_types],
            is_active=entity.is_active,
            contact_name=entity.contact_name,
            contact_email=entity.contact_email,
            contact_phone=entity.contact_phone,
            coverage_notes=entity.coverage_notes,
            rate_card_notes=entity.rate_card_notes,
            last_verified_at=ensure_utc(entity.last_verified_at)
            if entity.last_verified_at
            else None,
            deactivated_at=ensure_utc(entity.deactivated_at)
            if entity.deactivated_at
            else None,
            created_at=ensure_utc(entity.created_at),
            updated_at=ensure_utc(entity.updated_at),
        )


class WorkLifeReferralMapper:
    @staticmethod
    def to_entity(model: WorkLifeReferralModel) -> WorkLifeReferral:
        entity = WorkLifeReferral(
            id=WorkLifeReferralId(model.id),
            tenant_id=TenantId(model.tenant_id),
            clinical_subject_id=ClinicalSubjectId(model.clinical_subject_id),
            service_type=WorkLifeServiceType(model.service_type),
            requested_at=ensure_utc(model.requested_at),
            outcome=WorkLifeReferralOutcome(model.outcome),
            referred_provider_id=WorkLifeProviderId(model.referred_provider_id)
            if model.referred_provider_id
            else None,
            case_id=CaseId(model.case_id) if model.case_id else None,
            requested_by=UserId(model.requested_by)
            if model.requested_by
            else None,
            resolution_notes=model.resolution_notes,
            resolved_at=ensure_utc(model.resolved_at)
            if model.resolved_at
            else None,
            created_at=ensure_utc(model.created_at),
            updated_at=ensure_utc(model.updated_at),
        )
        entity.events.clear()
        return entity

    @staticmethod
    def to_model(entity: WorkLifeReferral) -> WorkLifeReferralModel:
        return WorkLifeReferralModel(
            id=entity.id.value,
            tenant_id=entity.tenant_id.value,
            clinical_subject_id=entity.clinical_subject_id.value,
            service_type=entity.service_type,
            requested_at=ensure_utc(entity.requested_at),
            outcome=entity.outcome,
            referred_provider_id=entity.referred_provider_id.value
            if entity.referred_provider_id
            else None,
            case_id=entity.case_id.value if entity.case_id else None,
            requested_by=entity.requested_by.value
            if entity.requested_by
            else None,
            resolution_notes=entity.resolution_notes,
            resolved_at=ensure_utc(entity.resolved_at)
            if entity.resolved_at
            else None,
            created_at=ensure_utc(entity.created_at),
            updated_at=ensure_utc(entity.updated_at),
        )


class TrainingEnrolmentMapper:
    @staticmethod
    def to_entity(model: TrainingEnrolmentModel) -> TrainingEnrolment:
        entity = TrainingEnrolment(
            id=TrainingEnrolmentId(model.id),
            tenant_id=TenantId(model.tenant_id),
            trainee_id=UserId(model.trainee_id),
            document_id=DocumentId(model.document_id),
            status=TrainingEnrolmentStatus(model.status),
            enrolled_at=ensure_utc(model.enrolled_at),
            completed_at=ensure_utc(model.completed_at)
            if model.completed_at
            else None,
            expires_on=model.expires_on,
            revoked_at=ensure_utc(model.revoked_at)
            if model.revoked_at
            else None,
            revoked_reason=model.revoked_reason,
            created_at=ensure_utc(model.created_at),
            updated_at=ensure_utc(model.updated_at),
        )
        entity.events.clear()
        return entity

    @staticmethod
    def to_model(entity: TrainingEnrolment) -> TrainingEnrolmentModel:
        return TrainingEnrolmentModel(
            id=entity.id.value,
            tenant_id=entity.tenant_id.value,
            trainee_id=entity.trainee_id.value,
            document_id=entity.document_id.value,
            status=entity.status,
            enrolled_at=ensure_utc(entity.enrolled_at),
            completed_at=ensure_utc(entity.completed_at)
            if entity.completed_at
            else None,
            expires_on=entity.expires_on,
            revoked_at=ensure_utc(entity.revoked_at)
            if entity.revoked_at
            else None,
            revoked_reason=entity.revoked_reason,
            created_at=ensure_utc(entity.created_at),
            updated_at=ensure_utc(entity.updated_at),
        )
