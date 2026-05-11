"""
Audit Mapper

Converts between Audit entities (domain) and Audit models (persistence).
"""

from app.domain.entities.audit import AuditLog, EntityChange
from app.domain.enums import AuditActionType
from app.domain.value_objects.audit import FieldChange
from app.domain.value_objects.core import (
    AuditLogId,
    EntityChangeId,
    TenantId,
    UserId,
)
from app.infrastructure.models.audit_model import AuditLogModel, EntityChangeModel
from app.shared.utils.datetime import ensure_utc, utc_now


class AuditMapper:
    """Mapper for Audit entities ↔ Audit models conversion"""

    @staticmethod
    def to_audit_log_entity(model: AuditLogModel) -> AuditLog:
        """
        Convert database model to domain entity.

        Args:
            model: AuditLogModel from database

        Returns:
            AuditLog with business logic
        """
        # Reconstruct value objects
        audit_log_id = AuditLogId(model.id)
        tenant_id = TenantId(model.tenant_id)
        user_id = UserId(model.user_id) if model.user_id else None

        # Reconstruct enums
        action_type = AuditActionType(model.action_type)

        # Create entity
        return AuditLog(
            id=audit_log_id,
            tenant_id=tenant_id,
            user_id=user_id,
            action_type=action_type,
            resource_type=model.resource_type,
            resource_id=model.resource_id,
            description=model.description,
            ip_address=model.ip_address,
            user_agent=model.user_agent,
            occurred_at=ensure_utc(model.occurred_at),
            metadata=model.extra_metadata,
            is_special_category=getattr(model, "is_special_category", False),
        )

    @staticmethod
    def to_audit_log_model(entity: AuditLog) -> AuditLogModel:
        """
        Convert domain entity to database model.

        Args:
            entity: AuditLog with business logic

        Returns:
            AuditLogModel for persistence
        """
        # Create model - convert metadata to plain dict for JSON serialization
        # (entity stores it as MappingProxyType for immutability, which is not JSON-serializable)
        metadata_dict = dict(entity._metadata) if entity._metadata else None

        # Create model
        return AuditLogModel(
            id=entity.id.value,
            tenant_id=entity.tenant_id.value,
            user_id=entity.user_id.value if entity.user_id else None,
            action_type=entity._action_type,
            resource_type=entity._resource_type,
            resourceid=entity._resource_id,
            description=entity.description,
            ip_address=entity._ip_address,
            user_agent=entity._user_agent,
            occurred_at=ensure_utc(entity.occurred_at),
            extrametadata=metadata_dict,
            is_special_category=getattr(entity, "is_special_category", False),
            created_at=ensure_utc(entity.occurred_at),
            updated_at=ensure_utc(entity.occurred_at),
        )

    @staticmethod
    def to_entity_change_entity(model: EntityChangeModel) -> EntityChange:
        """
        Convert database model to domain entity.

        Args:
            model: EntityChangeModel from database

        Returns:
            EntityChange with business logic
        """
        # Reconstruct value objects
        entity_change_id = EntityChangeId(model.id)
        audit_log_id = AuditLogId(model.audit_log_id)

        # Reconstruct field changes from JSON
        field_changes = tuple(
            FieldChange(
                field_name=fc["field_name"],
                old_value=fc.get("old_value"),
                new_value=fc.get("new_value"),
            )
            for fc in model.field_changes
        )

        # Create entity
        return EntityChange(
            id=entity_change_id,
            audit_log_id=audit_log_id,
            entity_type=model.entity_type,
            entity_id=model.entity_id,
            field_changes=field_changes,
        )

    @staticmethod
    def to_entity_change_model(entity: EntityChange) -> EntityChangeModel:
        """
        Convert domain entity to database model.

        Args:
            entity: EntityChange with business logic

        Returns:
            EntityChangeModel for persistence
        """
        # Serialize field changes to JSON
        field_changes = [
            {
                "field_name": fc.field_name,
                "old_value": fc.old_value,
                "new_value": fc.new_value,
            }
            for fc in entity._field_changes
        ]

        # Create model
        return EntityChangeModel(
            id=entity.id.value,
            audit_logid=entity._audit_log_id.value,
            entity_type=entity._entity_type,
            entityid=entity._entity_id,
            field_changes=field_changes,
            created_at=utc_now(),
            updated_at=utc_now(),
        )
