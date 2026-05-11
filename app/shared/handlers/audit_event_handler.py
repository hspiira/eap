"""Audit event handler (Phase 1 #C10).

Emits domain events to the transactional outbox; the worker drains the
outbox and writes the actual audit_logs / entity_changes rows. Writing to
the outbox happens in the caller's database transaction, so an event is
durable iff the action that produced it commits.
"""

from typing import Any

from app.domain.events import DomainEvent
from app.domain.repositories.outbox_repository import OutboxRepository
from app.domain.value_objects.core import TenantId, UserId
from app.shared.utils.audit_helper import (
    extract_field_changes,
    get_resource_id_from_entity,
    get_resource_type_from_entity,
    map_domain_event_to_audit_action,
)
from app.shared.utils.clinical_data_classification import is_special_category


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
            field_changes: list[dict[str, Any]] = []
            if action_type.value == "CREATE":
                field_changes = [
                    fc.__dict__ for fc in extract_field_changes(None, entity)
                ]
            elif action_type.value == "UPDATE" and old_entity is not None:
                field_changes = [
                    fc.__dict__ for fc in extract_field_changes(old_entity, entity)
                ]

            event_type_name = type(event).__name__
            payload = {
                "action_type": action_type.value,
                "resource_type": resource_type,
                "resource_id": resource_id,
                "user_id": user_id.value if user_id else None,
                "ip_address": ip_address,
                "user_agent": user_agent,
                "event_type": event_type_name,
                "event_data": _extract_event_data(event),
                "field_changes": field_changes,
                "is_special_category": is_special_category(
                    resource_type=resource_type, event_type=event_type_name
                ),
            }

            await self._outbox.enqueue(
                tenant_id=tenant_id.value,
                event_type=type(event).__name__,
                payload=payload,
                occurred_at=event.occurred_at,
                aggregate_type=resource_type,
                aggregate_id=resource_id,
            )


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
