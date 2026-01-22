"""
Audit Use Cases

Application services for Audit aggregate operations.
Refactored to use base use case classes.

Note: These use cases are primarily for logging actions.
They will be called by middleware/decorators, not directly via REST API.
"""

from typing import Any

from app.application.use_cases.base import BaseUseCase
from app.domain.entities.audit import AuditLog, EntityChange
from app.domain.enums import AuditActionType
from app.domain.repositories.audit_repository import AuditRepository
from app.domain.value_objects.audit import FieldChange
from app.domain.value_objects.core import (
    AuditLogId,
    EntityChangeId,
    TenantId,
    UserId,
)
from app.shared.utils.datetime import utc_now
from app.shared.utils.generators import generate_cuid


class LogAuditActionUseCase:
    """Use case for logging an audit action."""

    def __init__(self, audit_repository: AuditRepository):
        self.audit_repository = audit_repository

    async def execute(
        self,
        tenant_id: TenantId,
        action_type: AuditActionType,
        resource_type: str,
        user_id: UserId | None = None,
        resource_id: str | None = None,
        description: str | None = None,
        ip_address: str | None = None,
        user_agent: str | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> AuditLog:
        """Log an audit action."""
        audit_log = AuditLog(
            _id=AuditLogId(generate_cuid()),
            _tenant_id=tenant_id,
            _user_id=user_id,
            _action_type=action_type,
            _resource_type=resource_type,
            _resource_id=resource_id,
            _description=description,
            _ip_address=ip_address,
            _user_agent=user_agent,
            _occurred_at=utc_now(),
            _metadata=metadata,
        )

        await self.audit_repository.save_audit_log(audit_log)
        return audit_log


class LogEntityChangeUseCase:
    """Use case for logging entity changes."""

    def __init__(self, audit_repository: AuditRepository):
        self.audit_repository = audit_repository

    async def execute(
        self,
        audit_log_id: AuditLogId,
        entity_type: str,
        entity_id: str,
        field_changes: list[FieldChange],
    ) -> EntityChange:
        """Log entity changes associated with an audit log."""
        entity_change = EntityChange(
            _id=EntityChangeId(generate_cuid()),
            _audit_log_id=audit_log_id,
            _entity_type=entity_type,
            _entity_id=entity_id,
            _field_changes=tuple(field_changes),
        )

        await self.audit_repository.save_entity_change(entity_change)
        return entity_change


class GetAuditLogUseCase:
    """Use case for retrieving audit logs."""

    def __init__(self, audit_repository: AuditRepository):
        self.audit_repository = audit_repository

    async def execute(self, audit_log_id: AuditLogId) -> AuditLog | None:
        """Get audit log by ID."""
        return await self.audit_repository.get_audit_log_by_id(audit_log_id)

    async def execute_entity_changes(
        self, audit_log_id: AuditLogId
    ) -> list[EntityChange]:
        """Get all entity changes for an audit log."""
        changes = await self.audit_repository.get_entity_changes_by_audit_log_id(
            audit_log_id
        )
        return list(changes)

    async def execute_entity_history(
        self,
        tenant_id: TenantId,
        entity_type: str,
        entity_id: str,
        limit: int = 100,
        offset: int = 0,
    ) -> list[EntityChange]:
        """Get change history for a specific entity."""
        changes = await self.audit_repository.get_entity_changes_by_entity(
            tenant_id, entity_type, entity_id, limit, offset
        )
        return list(changes)
