"""
Industry API Schemas (DTOs)

Pydantic models for request/response validation.
"""

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from app.api.schemas.base import OptionalSanitizedStr, SanitizedStr


class IndustryCreate(BaseModel):
    """Request schema for creating an industry."""

    name: SanitizedStr = Field(..., min_length=1, max_length=255, description="Industry name")
    description: OptionalSanitizedStr = Field(None, description="Industry description")
    code: str | None = Field(None, max_length=50, description="Industry code")
    parent_industry_id: str | None = Field(None, description="Parent industry ID")


class IndustryUpdate(BaseModel):
    """Request schema for updating an industry."""

    name: OptionalSanitizedStr = Field(
        None, min_length=1, max_length=255, description="Industry name"
    )
    description: OptionalSanitizedStr = Field(None, description="Industry description")
    code: str | None = Field(None, max_length=50, description="Industry code")
    parent_industry_id: str | None = Field(None, description="Parent industry ID")


class IndustryResponse(BaseModel):
    """Response schema for industry."""

    id: str = Field(..., description="Industry identifier")
    tenant_id: str = Field(..., description="Tenant identifier")
    name: str = Field(..., description="Industry name")
    description: str | None = Field(None, description="Industry description")
    code: str | None = Field(None, description="Industry code")
    parent_industry_id: str | None = Field(None, description="Parent industry ID")
    is_active: bool = Field(..., description="Whether industry is active")
    created_at: datetime = Field(..., description="Creation timestamp")
    updated_at: datetime = Field(..., description="Last update timestamp")

    model_config = ConfigDict(from_attributes=True)


class IndustryListResponse(BaseModel):
    """Response schema for industry list."""

    items: list[IndustryResponse] = Field(..., description="List of industries")
    total: int = Field(..., description="Total number of industries matching filters")
    page: int = Field(..., description="Current page number")
    limit: int = Field(..., description="Items per page")
    has_more: bool = Field(..., description="Whether there are more items")
