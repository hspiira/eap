"""
Service Session Mapper

Converts between ServiceSessionEntity (domain) and ServiceSessionModel (persistence).
"""

from app.core.encryption import decrypt, encrypt
from app.domain.entities.service_session import ServiceSessionEntity
from app.domain.enums import SessionStatus
from app.domain.value_objects.core import (
    PersonId,
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
        provider_id = PersonId(model.provider_id)
        person_id = PersonId(model.person_id)

        # Reconstruct enums
        status = SessionStatus(model.status)

        # Create entity
        return ServiceSessionEntity(
            id=session_id,
            tenant_id=tenant_id,
            service_id=service_id,
            provider_id=provider_id,
            person_id=person_id,
            scheduled_at=ensure_utc(model.scheduled_at),
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
            deleted_at=ensure_utc(model.deleted_at) if model.deleted_at else None,
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
            person_id=entity.person_id.value,
            scheduled_at=ensure_utc(entity.scheduled_at),
            status=entity.status,
            reschedule_count=entity.reschedule_count,
            completed_at=ensure_utc(entity.completed_at) if entity.completed_at else None,
            duration=entity.duration,
            location=entity.location,
            notes=encrypt(entity.notes, tenant_id=entity.tenant_id.value),
            feedback=encrypt(entity.feedback, tenant_id=entity.tenant_id.value),
            cancellation_reason=entity.cancellation_reason,
            created_at=ensure_utc(entity.created_at),
            updated_at=ensure_utc(entity.updated_at),
            deleted_at=ensure_utc(entity.deleted_at) if entity.deleted_at else None,
        )
