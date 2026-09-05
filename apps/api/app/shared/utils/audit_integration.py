"""
Audit Integration Utilities

Helper functions for seamless audit integration in API routes.
"""

from typing import TYPE_CHECKING, Any

from fastapi import Request

if TYPE_CHECKING:
    pass
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
    events: list[Any] = getattr(entity, "events", None) or []
    if not events:
        return

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

    await audit_handler.handle_events(
        entity=entity,
        events=events.copy(),
        tenant_id=tenant_id,
        user_id=user_id,
        old_entity=old_entity,
        ip_address=ip_address,
        user_agent=user_agent,
    )

    events.clear()
