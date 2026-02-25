"""ServiceAssignment API Schemas (DTOs)."""

from datetime import datetime
from pydantic import BaseModel, ConfigDict, Field

from app.api.schemas.base import OptionalSanitizedStr
from app.domain.enums import BaseStatus


class ServiceAssignmentCreate(BaseModel):
    """Request schema for creating a service assignment."""

    service_id: str = Field(..., description="Service identifier")
    contract_id: str = Field(..., description="Contract identifier")
    notes: OptionalSanitizedStr = Field(None, description="Assignment notes")


class ServiceAssignmentUpdate(BaseModel):
    """Request schema for updating a service assignment."""

    notes: OptionalSanitizedStr = Field(None, description="Assignment notes")


class ServiceAssignmentResponse(BaseModel):
    """Response schema for service assignment."""

    id: str = Field(..., description="Assignment identifier")
    tenant_id: str = Field(..., description="Tenant identifier")
    service_id: str = Field(..., description="Service identifier")
    contract_id: str = Field(..., description="Contract identifier")
    status: BaseStatus = Field(..., description="Assignment status")
    assigned_at: datetime | None = Field(None, description="Assignment timestamp")
    assigned_by: str | None = Field(None, description="User who assigned")
    notes: str | None = Field(None, description="Assignment notes")
    is_active: bool = Field(..., description="Whether assignment is active")
    created_at: datetime = Field(..., description="Creation timestamp")
    updated_at: datetime = Field(..., description="Last update timestamp")

    model_config = ConfigDict(from_attributes=True)


class ServiceAssignmentListResponse(BaseModel):
    """Response schema for service assignment list."""

    items: list[ServiceAssignmentResponse] = Field(..., description="List of assignments")
    total: int = Field(..., description="Total number of assignments matching filters")
    page: int = Field(..., description="Current page number")
    limit: int = Field(..., description="Items per page")
    has_more: bool = Field(..., description="Whether there are more items")
