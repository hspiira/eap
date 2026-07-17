"""
Service API Schemas (DTOs)

Pydantic models for request/response validation.
Separate from domain entities.
"""

from pydantic import BaseModel, ConfigDict, Field

from app.api.schemas.base import OptionalSanitizedStr, SanitizedStr
from app.domain.enums import BaseStatus

# === Request Schemas ===

class ServiceCreate(BaseModel):
    """Request schema for creating a service."""

    name: SanitizedStr = Field(..., min_length=1, max_length=255, description="Service name")
    description: OptionalSanitizedStr = Field(None, max_length=2000, description="Service description")
    category: OptionalSanitizedStr = Field(None, max_length=100, description="Service category")
    duration_minutes: int | None = Field(None, gt=0, description="Service duration in minutes")
    is_group_service: bool = Field(False, description="Whether this is a group service")
    max_participants: int | None = Field(None, gt=0, description="Maximum participants for group services")


class ServiceUpdate(BaseModel):
    """Request schema for updating service information."""

    name: OptionalSanitizedStr = Field(None, min_length=1, max_length=255, description="Service name")
    description: OptionalSanitizedStr = Field(None, max_length=2000, description="Service description")
    category: OptionalSanitizedStr = Field(None, max_length=100, description="Service category")
    duration_minutes: int | None = Field(None, gt=0, description="Service duration in minutes")


class ServiceUpdateGroupSettings(BaseModel):
    """Request schema for updating group service settings."""

    is_group_service: bool = Field(..., description="Whether this is a group service")
    max_participants: int | None = Field(None, gt=0, description="Maximum participants for group services")


# === Response Schemas ===

class ServiceResponse(BaseModel):
    """Response schema for service."""

    id: str = Field(..., description="Service identifier")
    tenant_id: str = Field(..., description="Tenant identifier")
    name: str = Field(..., description="Service name")
    description: str | None = Field(None, description="Service description")
    category: str | None = Field(None, description="Service category")
    status: BaseStatus = Field(..., description="Service status")
    duration_minutes: int | None = Field(None, description="Service duration in minutes")
    is_group_service: bool = Field(..., description="Whether this is a group service")
    max_participants: int | None = Field(None, description="Maximum participants for group services")
    is_active: bool = Field(..., description="Whether service is active")

    model_config = ConfigDict(from_attributes=True)


class ServiceListResponse(BaseModel):
    """Response schema for service list."""

    items: list[ServiceResponse] = Field(..., description="List of services")
    total: int = Field(..., description="Total number of services matching filters")
    page: int = Field(..., description="Current page number")
    limit: int = Field(..., description="Items per page")
    has_more: bool = Field(..., description="Whether there are more items")
