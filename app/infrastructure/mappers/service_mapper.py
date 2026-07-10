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
            id=service_id,
            tenant_id=tenant_id,
            name=model.name,
            description=model.description,
            status=status,
            created_at=ensure_utc(model.created_at),
            updated_at=ensure_utc(model.updated_at),
            category=model.category,
            duration_minutes=model.duration_minutes,
            is_group_service=model.is_group_service,
            max_participants=model.max_participants,
            deleted_at=ensure_utc(model.deleted_at) if model.deleted_at else None,
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
            id=entity.id.value,
            tenant_id=entity.tenant_id.value,
            name=entity.name,
            description=entity.description,
            status=entity.status,
            category=entity.category,
            duration_minutes=entity.duration_minutes,
            is_group_service=entity.is_group_service,
            max_participants=entity.max_participants,
            created_at=ensure_utc(entity.created_at),
            updated_at=ensure_utc(entity.updated_at),
            deleted_at=ensure_utc(entity.deleted_at) if entity.deleted_at else None,
        )
