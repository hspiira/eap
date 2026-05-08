"""Outbox consumers (Phase 1 #C10).

Each consumer is an async function that takes an :class:`OutboxEventDTO`
and writes side-effects (audit row, notification, etc.). Consumers must be
idempotent: the dispatcher retries failed events with exponential backoff.
"""

from __future__ import annotations

from app.application.use_cases.audit_use_cases import (
    LogAuditActionUseCase,
    LogEntityChangeUseCase,
)
from app.domain.enums import AuditActionType
from app.domain.repositories.audit_repository import AuditRepository
from app.domain.repositories.outbox_repository import OutboxEventDTO
from app.domain.value_objects.audit import FieldChange
from app.domain.value_objects.core import TenantId, UserId


def make_audit_consumer(audit_repository: AuditRepository):
    log_action = LogAuditActionUseCase(audit_repository)
    log_changes = LogEntityChangeUseCase(audit_repository)

    async def consumer(event: OutboxEventDTO) -> None:
        payload = event.payload
        action_type = AuditActionType(payload["action_type"])
        user_id_value = payload.get("user_id")
        audit_log = await log_action.execute(
            tenant_id=TenantId(event.tenant_id),
            action_type=action_type,
            resource_type=payload["resource_type"],
            user_id=UserId(user_id_value) if user_id_value else None,
            resource_id=payload.get("resource_id"),
            description=f"{payload['event_type']} for {payload['resource_type']} {payload.get('resource_id')}",
            ip_address=payload.get("ip_address"),
            user_agent=payload.get("user_agent"),
            metadata={
                "event_type": payload["event_type"],
                "event_data": payload.get("event_data") or {},
            },
        )
        if audit_log is None:
            return
        field_changes_payload = payload.get("field_changes") or []
        if field_changes_payload:
            field_changes = [
                FieldChange(
                    field_name=fc["field_name"],
                    old_value=fc.get("old_value"),
                    new_value=fc.get("new_value"),
                )
                for fc in field_changes_payload
            ]
            await log_changes.execute(
                audit_log_id=audit_log.id,
                entity_type=payload["resource_type"],
                entity_id=payload.get("resource_id") or "",
                field_changes=field_changes,
            )

    return consumer
