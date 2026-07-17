"""
Route Audit Helper

Convenience functions for adding audit logging to API routes.
"""

from typing import Any

from fastapi import Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.value_objects.core import TenantId, UserId
from app.shared.handlers.audit_event_handler import AuditEventHandler
from app.shared.utils.audit_integration import process_entity_events_for_audit


async def audit_entity_operation(
    entity: Any,
    audit_handler: AuditEventHandler,
    tenant_id: TenantId | str,
    user_id: UserId | str | None = None,
    old_entity: Any | None = None,
    request: Request | None = None,
    db: AsyncSession | None = None,
) -> None:
    """
    Convenience function to audit an entity operation.

    This handles:
    - Converting string IDs to value objects
    - Processing domain events
    - Extracting context from request

    Usage in routes:
        await audit_entity_operation(
            entity=tenant,
            audit_handler=audit_handler,
            tenant_id=tenant.tenant_id,
            user_id=current_user_id,
            old_entity=old_tenant,
            request=request,
            db=db,
        )

    Args:
        entity: Entity that was modified
        audit_handler: Audit event handler
        tenant_id: Tenant ID (value object or string)
        user_id: User ID (value object or string, optional)
        old_entity: Previous entity state (for change tracking)
        request: FastAPI request (for IP/user agent)
        db: Database session (for committing audit logs)
    """
    if isinstance(tenant_id, str):
        tenant_id = TenantId(tenant_id)

    if user_id is not None and isinstance(user_id, str):
        user_id = UserId(user_id)

    await process_entity_events_for_audit(
        entity=entity,
        audit_handler=audit_handler,
        tenant_id=tenant_id,
        user_id=user_id,
        old_entity=old_entity,
        request=request,
    )


async def audit_change(
    entity: Any,
    audit_handler: AuditEventHandler,
    current_user: Any,
    request: Request | None = None,
    *,
    tenant_id: TenantId | str | None = None,
    old_entity: Any | None = None,
    db: AsyncSession | None = None,
) -> None:
    """
    Audit a mutation from a route.

    Thin wrapper over audit_entity_operation, which every route called with the
    same five arguments. `tenant_id` defaults to the entity's own; pass it where
    that isn't right (e.g. tenants, where the entity *is* the tenant).
    """
    await audit_entity_operation(
        entity=entity,
        audit_handler=audit_handler,
        tenant_id=tenant_id if tenant_id is not None else entity.tenant_id,
        user_id=getattr(current_user, "user_id", None) if current_user else None,
        old_entity=old_entity,
        request=request,
        db=db,
    )
