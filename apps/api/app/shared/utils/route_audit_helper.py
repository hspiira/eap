"""
Route Audit Helper

Convenience functions for adding audit logging to API routes.
"""

from typing import Any

from fastapi import Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.enums import AuditActionType
from app.domain.value_objects.core import TenantId, UserId
from app.shared.handlers.audit_event_handler import AuditEventHandler
from app.shared.utils.audit_helper import extract_field_changes
from app.shared.utils.audit_integration import (
    process_entity_events_for_audit,
    request_context,
)

PLATFORM_TENANT = "platform"
"""Tenant id for rows the platform owns rather than any one tenant.

The reference vocabularies are shared across tenants, so their audit rows
belong to none of them. `audit_logs.tenant_id` carries no foreign key for
exactly this reason; see docs/reviews/AUDIT_COVERAGE.md.
"""


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


_PAST_TENSE = {
    AuditActionType.CREATE: "Created",
    AuditActionType.UPDATE: "Updated",
    AuditActionType.DELETE: "Deleted",
    AuditActionType.LOGIN: "LoggedIn",
    AuditActionType.LOGOUT: "LoggedOut",
    AuditActionType.APPROVE: "Approved",
    AuditActionType.REJECT: "Rejected",
    AuditActionType.EXPORT: "Exported",
    AuditActionType.IMPORT: "Imported",
}


def event_name(resource_type: str, action: AuditActionType) -> str:
    """The event name a stated action is filed under, in the trail's own tense."""
    return f"{resource_type}{_PAST_TENSE.get(action, 'Changed')}"


async def audit_reference_change(
    audit_handler: AuditEventHandler,
    current_user: Any,
    request: Request | None = None,
    *,
    action: AuditActionType,
    resource_type: str,
    resource_id: str | None,
    before: Any | None = None,
    after: Any | None = None,
    tenant_id: TenantId | str = PLATFORM_TENANT,
) -> None:
    """Audit a write to a table that has no aggregate behind it.

    The reference vocabularies are rows a repository creates and updates
    directly, so there is no entity holding events for `audit_change` to
    drain. The action is stated by the caller and the diff is taken from the
    row itself.
    """
    ip_address, user_agent = request_context(request)
    await audit_handler.record_action(
        tenant_id=_tenant_id(tenant_id),
        action_type=action,
        resource_type=resource_type,
        resource_id=resource_id,
        event_type=event_name(resource_type, action),
        user_id=_user_id_of(current_user),
        ip_address=ip_address,
        user_agent=user_agent,
        field_changes=_reference_diff(before, after),
    )


async def audit_auth_event(
    audit_handler: AuditEventHandler,
    request: Request | None,
    *,
    action: AuditActionType,
    tenant_id: TenantId | str,
    user_id: UserId | str | None,
    outcome: str,
) -> None:
    """Audit a sign-in, sign-out or credential change.

    These routes hold no entity and often no authenticated caller, so the
    subject is named directly. `outcome` separates a granted sign-in from a
    refused one: both are recorded, and only the outcome tells them apart.
    """
    ip_address, user_agent = request_context(request)
    await audit_handler.record_action(
        tenant_id=_tenant_id(tenant_id),
        action_type=action,
        resource_type="Auth",
        resource_id=user_id.value if isinstance(user_id, UserId) else user_id,
        event_type=event_name("Auth", action),
        user_id=_user_id_of_value(user_id),
        ip_address=ip_address,
        user_agent=user_agent,
        event_data={"outcome": outcome},
    )


def _reference_diff(before: Any | None, after: Any | None) -> list[dict[str, Any]]:
    if after is None:
        return []
    return [fc.__dict__ for fc in extract_field_changes(before, after)]


def _tenant_id(value: TenantId | str) -> TenantId:
    return value if isinstance(value, TenantId) else TenantId(value)


def _user_id_of(current_user: Any) -> UserId | None:
    return _user_id_of_value(getattr(current_user, "user_id", None) if current_user else None)


def _user_id_of_value(value: UserId | str | None) -> UserId | None:
    if value is None or isinstance(value, UserId):
        return value
    return UserId(value) if value else None
