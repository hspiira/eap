"""ClientTag API Schemas (DTOs)."""

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from app.api.schemas.base import OptionalSanitizedStr, SanitizedStr


class ClientTagCreate(BaseModel):
    """Request schema for creating a client tag."""

    name: SanitizedStr = Field(..., min_length=1, max_length=255, description="Tag name")
    description: OptionalSanitizedStr = Field(None, description="Tag description")
    color: str | None = Field(None, max_length=7, pattern=r'^#([0-9A-Fa-f]{6})$', description="Hex color code (e.g., `#FF5733`)")


class ClientTagUpdate(BaseModel):
    """Request schema for updating a client tag."""

    name: OptionalSanitizedStr = Field(None, min_length=1, max_length=255, description="Tag name")
    description: OptionalSanitizedStr = Field(None, description="Tag description")
    color: str | None = Field(None, max_length=7, pattern=r'^#([0-9A-Fa-f]{6})$', description="Hex color code (e.g., `#FF5733`)")


class ClientTagResponse(BaseModel):
    """Response schema for client tag."""

    id: str = Field(..., description="Tag identifier")
    tenant_id: str = Field(..., description="Tenant identifier")
    name: str = Field(..., description="Tag name")
    description: str | None = Field(None, description="Tag description")
    color: str | None = Field(None, max_length=7, pattern=r'^#([0-9A-Fa-f]{6})$', description="Hex color code (e.g., `#FF5733`)")
    is_active: bool = Field(..., description="Whether tag is active")
    created_at: datetime = Field(..., description="Creation timestamp")
    updated_at: datetime = Field(..., description="Last update timestamp")

    model_config = ConfigDict(from_attributes=True)


class ClientTagListResponse(BaseModel):
    """Response schema for client tag list."""

    items: list[ClientTagResponse] = Field(..., description="List of tags")
    total: int = Field(..., description="Total number of tags matching filters")
    page: int = Field(..., description="Current page number")
    limit: int = Field(..., description="Items per page")
    has_more: bool = Field(..., description="Whether there are more items")
