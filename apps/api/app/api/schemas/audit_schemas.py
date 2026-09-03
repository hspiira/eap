"""
Audit API Schemas (DTOs)

Pydantic models for request/response validation.
Separate from domain entities.

Note: Audit logs are immutable - only read operations via API.
"""

from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from app.domain.enums import AuditActionType

# === Value Object Schemas ===


class FieldChangeSchema(BaseModel):
    """Field change schema."""

    field_name: str = Field(..., description="Field name")
    old_value: str | None = Field(None, description="Old value")
    new_value: str | None = Field(None, description="New value")

    model_config = ConfigDict(from_attributes=True)


# === Response Schemas ===


class EntityChangeResponse(BaseModel):
    """Response schema for entity change."""

    id: str = Field(..., description="Entity change identifier")
    audit_log_id: str = Field(..., description="Associated audit log identifier")
    entity_type: str = Field(..., description="Entity type")
    entity_id: str = Field(..., description="Entity identifier")
    field_changes: list[FieldChangeSchema] = Field(..., description="Field changes")

    model_config = ConfigDict(from_attributes=True)


class AuditLogResponse(BaseModel):
    """Response schema for audit log."""

    id: str = Field(..., description="Audit log identifier")
    tenant_id: str = Field(..., description="Tenant identifier")
    user_id: str | None = Field(None, description="User identifier")
    action_type: AuditActionType = Field(..., description="Action type")
    resource_type: str = Field(..., description="Resource type")
    resource_id: str | None = Field(None, description="Resource identifier")
    description: str | None = Field(None, description="Action description")
    ip_address: str | None = Field(None, description="IP address")
    user_agent: str | None = Field(None, description="User agent")
    occurred_at: datetime = Field(..., description="When the action occurred")
    metadata: dict[str, Any] | None = Field(None, description="Additional metadata")

    model_config = ConfigDict(from_attributes=True)


class AuditLogListResponse(BaseModel):
    """Response schema for audit log list."""

    items: list[AuditLogResponse] = Field(..., description="List of audit logs")
    total: int = Field(..., description="Total number of audit logs matching filters")
    page: int = Field(..., description="Current page number")
    limit: int = Field(..., description="Items per page")
    has_more: bool = Field(..., description="Whether there are more items")


class EntityChangeListResponse(BaseModel):
    """Response schema for entity change list."""

    items: list[EntityChangeResponse] = Field(..., description="List of entity changes")
    total: int = Field(..., description="Total number of entity changes")
    page: int = Field(..., description="Current page number")
    limit: int = Field(..., description="Items per page")
    has_more: bool = Field(..., description="Whether there are more items")
