"""
Audit Integration Utilities

Helper functions for seamless audit integration in API routes.
"""

from typing import Any

from fastapi import Request

from app.domain.entities.audit import AuditLog
from app.domain.value_objects.core import TenantId, UserId
from app.shared.handlers.audit_event_handler import AuditEventHandler


async def process_entity_events_for_audit(
    entity: Any,
    audit_handler: AuditEventHandler,
    tenant_id: TenantId,
    user_id: UserId | None = None,
    old_entity: Any | None = None,
    request: Request | None = None,
) -> None:
    """
    Process entity events and create audit logs.
    
    This is a convenience function to be called after entity operations.
    
    Args:
        entity: Entity that was modified
        audit_handler: Audit event handler
        tenant_id: Tenant identifier
        user_id: User identifier (None for system actions)
        old_entity: Previous entity state (for tracking changes)
        request: FastAPI request (for extracting IP/user agent)
    """
    if not hasattr(entity, "_events") or not entity._events:
        return

    # Extract IP and user agent from request if available
    ip_address = None
    user_agent = None
    if request:
        # Extract IP address
        forwarded = request.headers.get("x-forwarded-for")
        if forwarded:
            ip_address = forwarded.split(",")[0].strip()
        else:
            real_ip = request.headers.get("x-real-ip")
            if real_ip:
                ip_address = real_ip
            elif request.client:
                ip_address = request.client.host

        # Extract user agent
        user_agent = request.headers.get("user-agent")

    # Process events
    await audit_handler.handle_events(
        entity=entity,
        events=entity._events.copy(),  # Copy to avoid mutation
        tenant_id=tenant_id,
        user_id=user_id,
        old_entity=old_entity,
        ip_address=ip_address,
        user_agent=user_agent,
    )

    # Clear events after processing
    entity._events.clear()


async def log_audit_action_directly(
    audit_handler: AuditEventHandler,
    tenant_id: TenantId,
    action_type: str,
    resource_type: str,
    user_id: UserId | None = None,
    resource_id: str | None = None,
    description: str | None = None,
    request: Request | None = None,
    metadata: dict[str, Any] | None = None,
) -> AuditLog:
    """
    Log an audit action directly (for actions that don't raise domain events).
    
    Args:
        audit_handler: Audit event handler
        tenant_id: Tenant identifier
        action_type: Action type (from AuditActionType enum)
        resource_type: Resource type (e.g., "Tenant", "Person")
        user_id: User identifier
        resource_id: Resource identifier
        description: Action description
        request: FastAPI request (for extracting IP/user agent)
        metadata: Additional metadata
        
    Returns:
        Created AuditLog
    """
    from app.application.use_cases.audit_use_cases import LogAuditActionUseCase
    from app.domain.enums import AuditActionType

    # Extract IP and user agent from request if available
    ip_address = None
    user_agent = None
    if request:
        forwarded = request.headers.get("x-forwarded-for")
        if forwarded:
            ip_address = forwarded.split(",")[0].strip()
        else:
            real_ip = request.headers.get("x-real-ip")
            if real_ip:
                ip_address = real_ip
            elif request.client:
                ip_address = request.client.host
        user_agent = request.headers.get("user-agent")

    log_use_case = LogAuditActionUseCase(audit_handler.audit_repository)

    # Convert string to enum if needed
    if isinstance(action_type, str):
        action_type = AuditActionType[action_type]

    return await log_use_case.execute(
        tenant_id=tenant_id,
        action_type=action_type,
        resource_type=resource_type,
        user_id=user_id,
        resource_id=resource_id,
        description=description,
        ip_address=ip_address,
        user_agent=user_agent,
        metadata=metadata,
    )
