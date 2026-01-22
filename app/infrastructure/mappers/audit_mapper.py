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
            _id=audit_log_id,
            _tenant_id=tenant_id,
            _user_id=user_id,
            _action_type=action_type,
            _resource_type=model.resource_type,
            _resource_id=model.resource_id,
            _description=model.description,
            _ip_address=model.ip_address,
            _user_agent=model.user_agent,
            _occurred_at=ensure_utc(model.occurred_at),
            _metadata=model.metadata,
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
        # Create model
        return AuditLogModel(
            id=entity._id.value,
            tenant_id=entity._tenant_id.value,
            user_id=entity._user_id.value if entity._user_id else None,
            action_type=entity._action_type,
            resource_type=entity._resource_type,
            resource_id=entity._resource_id,
            description=entity._description,
            ip_address=entity._ip_address,
            user_agent=entity._user_agent,
            occurred_at=ensure_utc(entity._occurred_at),
            metadata=entity._metadata,
            created_at=ensure_utc(entity._occurred_at),  # Use occurred_at for created_at
            updated_at=ensure_utc(entity._occurred_at),  # Immutable, so same as created_at
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
            _id=entity_change_id,
            _audit_log_id=audit_log_id,
            _entity_type=model.entity_type,
            _entity_id=model.entity_id,
            _field_changes=field_changes,
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
            id=entity._id.value,
            audit_log_id=entity._audit_log_id.value,
            entity_type=entity._entity_type,
            entity_id=entity._entity_id,
            field_changes=field_changes,
            created_at=utc_now(),
            updated_at=utc_now(),
        )
