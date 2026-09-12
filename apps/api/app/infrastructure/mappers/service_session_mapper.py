"""
Service Session Mapper

Converts between ServiceSessionEntity (domain) and ServiceSessionModel (persistence).
"""

from app.core.encryption import decrypt, encrypt
from app.domain.entities.service_session import ServiceSessionEntity
from app.domain.enums import (
    ClientType,
    SessionAttendance,
    SessionCategory,
    SessionClinicalStatus,
    SessionDeliveryContext,
    SessionStatus,
    SessionType,
)
from app.domain.value_objects.core import (
    ClientId,
    ContractId,
    EligibleMemberId,
    ProviderId,
    ServiceId,
    SessionId,
    TenantId,
)
from app.infrastructure.models.service_session_model import ServiceSessionModel
from app.shared.utils.datetime import ensure_utc


class ServiceSessionMapper:
    """Mapper for ServiceSessionEntity ↔ ServiceSessionModel conversion"""

    @staticmethod
    def to_entity(model: ServiceSessionModel) -> ServiceSessionEntity:
        """
        Convert database model to domain entity.

        Args:
            model: ServiceSessionModel from database

        Returns:
            ServiceSessionEntity with business logic
        """
        # Reconstruct value objects
        session_id = SessionId(model.id)
        tenant_id = TenantId(model.tenant_id)
        service_id = ServiceId(model.service_id)
        provider_id = ProviderId(model.provider_id)
        member_id = EligibleMemberId(model.member_id) if model.member_id else None

        # Reconstruct enums
        status = SessionStatus(model.status)

        # Create entity
        return ServiceSessionEntity(
            id=session_id,
            tenant_id=tenant_id,
            service_id=service_id,
            provider_id=provider_id,
            client_id=ClientId(model.client_id),
            contract_id=ContractId(model.contract_id) if model.contract_id else None,
            attendance=SessionAttendance(model.attendance),
            member_id=member_id,
            scheduled_at=ensure_utc(model.scheduled_at),
            # An absent value reads as Unknown, never as Direct: decision 2 forbids
            # inferring a direct arrangement from a missing one.
            delivery_context=SessionDeliveryContext(
                model.delivery_context or SessionDeliveryContext.UNKNOWN
            ),
            provider_affiliation_id=model.provider_affiliation_id,
            status=status,
            created_at=ensure_utc(model.created_at),
            updated_at=ensure_utc(model.updated_at),
            reschedule_count=model.reschedule_count,
            completed_at=ensure_utc(model.completed_at) if model.completed_at else None,
            duration=model.duration,
            location=model.location,
            notes=decrypt(model.notes, tenant_id=model.tenant_id),
            feedback=decrypt(model.feedback, tenant_id=model.tenant_id),
            cancellation_reason=model.cancellation_reason,
            incident_id=getattr(model, "incident_id", None),
            follow_up_of_session_id=(
                SessionId(model.follow_up_of_session_id) if model.follow_up_of_session_id else None
            ),
            deleted_at=ensure_utc(model.deleted_at) if model.deleted_at else None,
            session_type=SessionType(model.session_type) if model.session_type else None,
            category=SessionCategory(model.category) if model.category else None,
            rate_ugx=model.rate_ugx,
            issue_topic=decrypt(model.issue_topic, tenant_id=model.tenant_id),
            diagnosis_type_id=model.diagnosis_type_id,
            diagnosis_id=model.diagnosis_id,
            approved_by=model.approved_by,
            session_number=model.session_number,
            partner_name=decrypt(model.partner_name, tenant_id=model.tenant_id),
            partner_relationship=model.partner_relationship,
            headcount=model.headcount,
            client_type=ClientType(model.client_type) if model.client_type else None,
            clinical_outcome=SessionClinicalStatus(model.clinical_outcome)
            if model.clinical_outcome
            else None,
        )

    @staticmethod
    def to_model(entity: ServiceSessionEntity) -> ServiceSessionModel:
        """
        Convert domain entity to database model.

        Args:
            entity: ServiceSessionEntity with business logic

        Returns:
            ServiceSessionModel for persistence
        """
        # Create model
        return ServiceSessionModel(
            id=entity.id.value,
            tenant_id=entity.tenant_id.value,
            service_id=entity.service_id.value,
            provider_id=entity.provider_id.value,
            client_id=entity.client_id.value,
            contract_id=entity.contract_id.value if entity.contract_id else None,
            attendance=entity.attendance,
            member_id=entity.member_id.value if entity.member_id else None,
            scheduled_at=ensure_utc(entity.scheduled_at),
            delivery_context=entity.delivery_context,
            provider_affiliation_id=entity.provider_affiliation_id,
            status=entity.status,
            reschedule_count=entity.reschedule_count,
            completed_at=ensure_utc(entity.completed_at) if entity.completed_at else None,
            duration=entity.duration,
            location=entity.location,
            notes=encrypt(entity.notes, tenant_id=entity.tenant_id.value),
            feedback=encrypt(entity.feedback, tenant_id=entity.tenant_id.value),
            cancellation_reason=entity.cancellation_reason,
            incident_id=entity.incident_id,
            follow_up_of_session_id=(
                entity.follow_up_of_session_id.value if entity.follow_up_of_session_id else None
            ),
            created_at=ensure_utc(entity.created_at),
            updated_at=ensure_utc(entity.updated_at),
            deleted_at=ensure_utc(entity.deleted_at) if entity.deleted_at else None,
            session_type=entity.session_type,
            category=entity.category,
            rate_ugx=entity.rate_ugx,
            issue_topic=encrypt(entity.issue_topic, tenant_id=entity.tenant_id.value),
            diagnosis_type_id=entity.diagnosis_type_id,
            diagnosis_id=entity.diagnosis_id,
            approved_by=entity.approved_by,
            session_number=entity.session_number,
            partner_name=encrypt(entity.partner_name, tenant_id=entity.tenant_id.value),
            partner_relationship=entity.partner_relationship,
            headcount=entity.headcount,
            client_type=entity.client_type,
            clinical_outcome=entity.clinical_outcome,
        )
