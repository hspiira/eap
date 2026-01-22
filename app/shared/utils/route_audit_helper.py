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
            tenant_id=tenant._tenant_id,
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
    # Convert string IDs to value objects if needed
    if isinstance(tenant_id, str):
        tenant_id = TenantId(tenant_id)
    
    if user_id is not None and isinstance(user_id, str):
        user_id = UserId(user_id)

    # Process events
    await process_entity_events_for_audit(
        entity=entity,
        audit_handler=audit_handler,
        tenant_id=tenant_id,
        user_id=user_id,
        old_entity=old_entity,
        request=request,
    )

    # Note: Audit logs are committed separately
    # The db session here is for the main transaction
    # Audit should be in a separate transaction or committed after main commit
