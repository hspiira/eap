"""
Service Mapper

Converts between ServiceEntity (domain) and ServiceModel (persistence).
"""

from app.domain.entities.service import ServiceEntity
from app.domain.enums import BaseStatus
from app.domain.value_objects.core import ServiceId, TenantId
from app.infrastructure.models.service_model import ServiceModel
from app.shared.utils.datetime import ensure_utc


class ServiceMapper:
    """Mapper for ServiceEntity ↔ ServiceModel conversion"""

    @staticmethod
    def to_entity(model: ServiceModel) -> ServiceEntity:
        """
        Convert database model to domain entity.

        Args:
            model: ServiceModel from database

        Returns:
            ServiceEntity with business logic
        """
        # Reconstruct value objects
        service_id = ServiceId(model.id)
        tenant_id = TenantId(model.tenant_id)

        # Reconstruct enums
        status = BaseStatus(model.status)

        # Create entity
        return ServiceEntity(
            _id=service_id,
            _tenant_id=tenant_id,
            _name=model.name,
            _description=model.description,
            _status=status,
            _created_at=ensure_utc(model.created_at),
            _updated_at=ensure_utc(model.updated_at),
            _category=model.category,
            _duration_minutes=model.duration_minutes,
            _is_group_service=model.is_group_service,
            _max_participants=model.max_participants,
            _deleted_at=ensure_utc(model.deleted_at) if model.deleted_at else None,
        )

    @staticmethod
    def to_model(entity: ServiceEntity) -> ServiceModel:
        """
        Convert domain entity to database model.

        Args:
            entity: ServiceEntity with business logic

        Returns:
            ServiceModel for persistence
        """
        # Create model
        return ServiceModel(
            id=entity._id.value,
            tenant_id=entity._tenant_id.value,
            name=entity._name,
            description=entity._description,
            status=entity._status,
            category=entity._category,
            duration_minutes=entity._duration_minutes,
            is_group_service=entity._is_group_service,
            max_participants=entity._max_participants,
            created_at=ensure_utc(entity._created_at),
            updated_at=ensure_utc(entity._updated_at),
            deleted_at=ensure_utc(entity._deleted_at) if entity._deleted_at else None,
        )
