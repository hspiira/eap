"""Audit event handler (Phase 1 #C10).

Emits domain events to the transactional outbox; the worker drains the
outbox and writes the actual audit_logs / entity_changes rows. Writing to
the outbox happens in the caller's database transaction, so an event is
durable iff the action that produced it commits.
"""

from datetime import datetime
from typing import Any

from app.domain.enums import AuditActionType
from app.domain.events import DomainEvent
from app.domain.repositories.outbox_repository import OutboxRepository
from app.domain.value_objects.core import TenantId, UserId
from app.shared.utils.audit_helper import (
    extract_field_changes,
    get_resource_id_from_entity,
    get_resource_type_from_entity,
    map_domain_event_to_audit_action,
    redact_values,
)
from app.shared.utils.clinical_data_classification import (
    is_special_category,
    redacts_content,
)
from app.shared.utils.datetime import utc_now


class AuditEventHandler:
    """Enqueues domain events on the transactional outbox."""

    def __init__(self, outbox_repository: OutboxRepository):
        self._outbox = outbox_repository

    async def handle_events(
        self,
        entity: Any,
        events: list[DomainEvent],
        tenant_id: TenantId,
        user_id: UserId | None = None,
        old_entity: Any | None = None,
        ip_address: str | None = None,
        user_agent: str | None = None,
    ) -> None:
        if not events:
            return

        resource_type = get_resource_type_from_entity(entity)
        resource_id = get_resource_id_from_entity(entity)

        for event in events:
            action_type = map_domain_event_to_audit_action(type(event).__name__)
            await self._enqueue(
                tenant_id=tenant_id,
                action_type=action_type,
                resource_type=resource_type,
                resource_id=resource_id,
                event_type=type(event).__name__,
                event_data=_extract_event_data(event),
                field_changes=_diff_for(action_type, entity, old_entity),
                occurred_at=event.occurred_at,
                user_id=user_id,
                ip_address=ip_address,
                user_agent=user_agent,
            )

    async def record_action(
        self,
        *,
        tenant_id: TenantId,
        action_type: AuditActionType,
        resource_type: str,
        resource_id: str | None,
        event_type: str,
        user_id: UserId | None = None,
        ip_address: str | None = None,
        user_agent: str | None = None,
        event_data: dict[str, Any] | None = None,
        field_changes: list[dict[str, Any]] | None = None,
    ) -> None:
        """Record a write that no domain event covers.

        Reference tables and the auth routes mutate rows without an aggregate
        to append to, so the action is stated here instead of derived from an
        event. Everything downstream is identical: the same outbox, the same
        payload, the same worker.
        """
        await self._enqueue(
            tenant_id=tenant_id,
            action_type=action_type,
            resource_type=resource_type,
            resource_id=resource_id,
            event_type=event_type,
            event_data=event_data or {},
            field_changes=field_changes or [],
            occurred_at=utc_now(),
            user_id=user_id,
            ip_address=ip_address,
            user_agent=user_agent,
        )

    async def _enqueue(
        self,
        *,
        tenant_id: TenantId,
        action_type: AuditActionType,
        resource_type: str,
        resource_id: str | None,
        event_type: str,
        event_data: dict[str, Any],
        field_changes: list[dict[str, Any]],
        occurred_at: datetime,
        user_id: UserId | None,
        ip_address: str | None,
        user_agent: str | None,
    ) -> None:
        if redacts_content(resource_type):
            field_changes = redact_values(field_changes)
        payload = {
            "action_type": action_type.value,
            "resource_type": resource_type,
            "resource_id": resource_id,
            "user_id": user_id.value if user_id else None,
            "ip_address": ip_address,
            "user_agent": user_agent,
            "event_type": event_type,
            "event_data": event_data,
            "field_changes": field_changes,
            "is_special_category": is_special_category(
                resource_type=resource_type, event_type=event_type
            ),
        }
        await self._outbox.enqueue(
            tenant_id=tenant_id.value,
            event_type=event_type,
            payload=payload,
            occurred_at=occurred_at,
            aggregate_type=resource_type,
            aggregate_id=resource_id,
        )


def _diff_for(
    action_type: AuditActionType, entity: Any, old_entity: Any | None
) -> list[dict[str, Any]]:
    if action_type == AuditActionType.CREATE:
        return [fc.__dict__ for fc in extract_field_changes(None, entity)]
    if action_type == AuditActionType.UPDATE and old_entity is not None:
        return [fc.__dict__ for fc in extract_field_changes(old_entity, entity)]
    return []


def _extract_event_data(event: DomainEvent) -> dict[str, Any]:
    data: dict[str, Any] = {}
    for field_name, field_value in event.__dict__.items():
        if field_name == "occurred_at":
            continue
        if hasattr(field_value, "value"):
            data[field_name] = field_value.value
        elif hasattr(field_value, "isoformat"):
            data[field_name] = field_value.isoformat()
        else:
            data[field_name] = str(field_value)
    return data
