"""
Audit Event Handler

Handles domain events and automatically creates audit logs.
"""

from typing import Any

from app.application.use_cases.audit_use_cases import (
    LogAuditActionUseCase,
    LogEntityChangeUseCase,
)
from app.domain.enums import AuditActionType
from app.domain.events import DomainEvent
from app.domain.repositories.audit_repository import AuditRepository
from app.domain.value_objects.core import TenantId, UserId
from app.shared.utils.audit_helper import (
    extract_field_changes,
    get_resource_id_from_entity,
    get_resource_type_from_entity,
    map_domain_event_to_audit_action,
)


class AuditEventHandler:
    """
    Event handler that processes domain events and creates audit logs.
    
    This should be called after entity operations to process collected events.
    """

    def __init__(self, audit_repository: AuditRepository):
        self.audit_repository = audit_repository

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
        """
        Process domain events and create audit logs.
        
        Args:
            entity: Entity that raised the events
            events: List of domain events
            tenant_id: Tenant identifier
            user_id: User identifier (None for system actions)
            old_entity: Previous entity state (for tracking changes)
            ip_address: IP address
            user_agent: User agent string
        """
        if not events:
            return

        log_use_case = LogAuditActionUseCase(self.audit_repository)
        change_use_case = LogEntityChangeUseCase(self.audit_repository)

        resource_type = get_resource_type_from_entity(entity)
        resource_id = get_resource_id_from_entity(entity)

        for event in events:
            action_type = map_domain_event_to_audit_action(type(event).__name__)

            audit_log = await log_use_case.execute(
                tenant_id=tenant_id,
                action_type=action_type,
                resource_type=resource_type,
                user_id=user_id,
                resource_id=resource_id,
                description=f"{type(event).__name__} for {resource_type} {resource_id}",
                ip_address=ip_address,
                user_agent=user_agent,
                metadata={
                    "event_type": type(event).__name__,
                    "event_data": self._extract_event_data(event),
                },
            )

            if audit_log is not None:
                if action_type == AuditActionType.CREATE:
                    field_changes = extract_field_changes(None, entity)
                elif action_type == AuditActionType.UPDATE and old_entity is not None:
                    field_changes = extract_field_changes(old_entity, entity)
                else:
                    field_changes = []
                
                if field_changes:
                    await change_use_case.execute(
                        audit_log_id=audit_log._id,
                        entity_type=resource_type,
                        entity_id=resource_id or "",
                        field_changes=field_changes,
                    )

    def _extract_event_data(self, event: DomainEvent) -> dict[str, Any]:
        """Extract relevant data from domain event."""
        data = {}
        for field_name, field_value in event.__dict__.items():
            if field_name == "occurred_at":
                continue
            if hasattr(field_value, "value"):
                data[field_name] = field_value.value
            else:
                data[field_name] = str(field_value)
        return data
