"""
Audit Entities

Immutable audit log entities for tracking system-wide events and changes.
"""

from dataclasses import dataclass
from datetime import datetime
from typing import Any

from app.domain.enums import AuditActionType
from app.domain.value_objects.audit import FieldChange
from app.domain.value_objects.core import AuditLogId, EntityChangeId, TenantId, UserId


@dataclass(frozen=True)
class EntityChange:
    """
    Represents detailed changes to an entity.
    
    Immutable aggregate that tracks field-level changes.
    """
    _id: EntityChangeId
    _audit_log_id: AuditLogId
    _entity_type: str  # e.g., "Tenant", "Person", "Client"
    _entity_id: str
    _field_changes: tuple[FieldChange, ...]  # Immutable tuple
    
    def __post_init__(self) -> None:
        """Validate entity change."""
        if not self._entity_type:
            raise ValueError("Entity type cannot be empty")
        if not self._entity_id:
            raise ValueError("Entity ID cannot be empty")


@dataclass(frozen=True)
class AuditLog:
    """
    High-level audit log entry.
    
    Immutable aggregate root for audit tracking.
    All audit logs are immutable - no updates or deletes allowed.
    """
    _id: AuditLogId
    _tenant_id: TenantId
    _user_id: UserId | None  # None for system actions
    _action_type: AuditActionType
    _resource_type: str  # e.g., "Tenant", "Person", "Client", "Contract"
    _resource_id: str | None  # None for actions that don't target a resource
    _description: str | None
    _ip_address: str | None
    _user_agent: str | None
    _occurred_at: datetime
    _metadata: dict[str, Any] | None  # Additional context
    
    def __post_init__(self) -> None:
        """Validate audit log."""
        if not self._resource_type:
            raise ValueError("Resource type cannot be empty")
    
    def has_changes(self) -> bool:
        """Check if this audit log has associated entity changes."""
        # This would be checked via repository
        return False  # Placeholder - actual check in repository
