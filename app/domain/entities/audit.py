"""
Audit Entities

Immutable audit log entities for tracking system-wide events and changes.
"""

from dataclasses import dataclass
from datetime import datetime
from types import MappingProxyType
from typing import Any, Mapping

from app.domain.enums import AuditActionType
from app.domain.value_objects.audit import FieldChange
from app.domain.value_objects.core import AuditLogId, EntityChangeId, TenantId, UserId


@dataclass(frozen=True)
class EntityChange:
    """Detailed changes to an entity. Immutable; tracks field-level changes."""

    id: EntityChangeId
    audit_log_id: AuditLogId
    entity_type: str
    entity_id: str
    field_changes: tuple[FieldChange, ...]

    def __post_init__(self) -> None:
        if not self.entity_type:
            raise ValueError("Entity type cannot be empty")
        if not self.entity_id:
            raise ValueError("Entity ID cannot be empty")


@dataclass(frozen=True)
class AuditLog:
    """High-level audit log entry. Immutable; never updated or deleted."""

    id: AuditLogId
    tenant_id: TenantId
    user_id: UserId | None
    action_type: AuditActionType
    resource_type: str
    resource_id: str | None
    description: str | None
    ip_address: str | None
    user_agent: str | None
    occurred_at: datetime
    metadata: Mapping[str, Any] | None

    def __post_init__(self) -> None:
        if not self.resource_type:
            raise ValueError("Resource type cannot be empty")
        if isinstance(self.metadata, dict):
            object.__setattr__(self, "metadata", MappingProxyType(self.metadata))

    def has_changes(self) -> bool:
        return False
