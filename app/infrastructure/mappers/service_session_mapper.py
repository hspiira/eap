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
            _id=session_id,
            _tenant_id=tenant_id,
            _service_id=service_id,
            _provider_id=provider_id,
            _person_id=person_id,
            _scheduled_at=ensure_utc(model.scheduled_at),
            _status=status,
            _created_at=ensure_utc(model.created_at),
            _updated_at=ensure_utc(model.updated_at),
            _reschedule_count=model.reschedule_count,
            _completed_at=ensure_utc(model.completed_at) if model.completed_at else None,
            _duration=model.duration,
            _location=model.location,
            _notes=decrypt(model.notes, tenant_id=model.tenant_id),
            _feedback=decrypt(model.feedback, tenant_id=model.tenant_id),
            _cancellation_reason=model.cancellation_reason,
            _deleted_at=ensure_utc(model.deleted_at) if model.deleted_at else None,
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
            id=entity._id.value,
            tenant_id=entity._tenant_id.value,
            service_id=entity._service_id.value,
            provider_id=entity._provider_id.value,
            person_id=entity._person_id.value,
            scheduled_at=ensure_utc(entity._scheduled_at),
            status=entity._status,
            reschedule_count=entity._reschedule_count,
            completed_at=ensure_utc(entity._completed_at) if entity._completed_at else None,
            duration=entity._duration,
            location=entity._location,
            notes=encrypt(entity._notes, tenant_id=entity._tenant_id.value),
            feedback=encrypt(entity._feedback, tenant_id=entity._tenant_id.value),
            cancellation_reason=entity._cancellation_reason,
            created_at=ensure_utc(entity._created_at),
            updated_at=ensure_utc(entity._updated_at),
            deleted_at=ensure_utc(entity._deleted_at) if entity._deleted_at else None,
        )
