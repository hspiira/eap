"""Activity API Schemas (DTOs)."""

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class ActivityCreate(BaseModel):
    """Request schema for creating an activity."""

    client_id: str = Field(..., description="Associated client ID")
    activity_type: str = Field(..., max_length=50, description="Activity type")
    subject: str | None = Field(None, max_length=255, description="Activity subject")
    description: str = Field(..., description="Activity description")
    outcome: str | None = Field(None, description="Activity outcome")
    occurred_at: datetime = Field(..., description="When the activity occurred")
    next_follow_up: datetime | None = Field(None, description="Next follow-up date")
    is_important: bool = Field(False, description="Whether activity is important")


class ActivityUpdate(BaseModel):
    """Request schema for updating an activity."""

    description: str | None = Field(None, description="Activity description")
    outcome: str | None = Field(None, description="Activity outcome")
    next_follow_up: datetime | None = Field(None, description="Next follow-up date")
    is_important: bool | None = Field(None, description="Whether activity is important")


class ActivityResponse(BaseModel):
    """Response schema for activity."""

    id: str = Field(..., description="Activity identifier")
    tenant_id: str = Field(..., description="Tenant identifier")
    client_id: str = Field(..., description="Associated client ID")
    activity_type: str = Field(..., description="Activity type")
    subject: str | None = Field(None, description="Activity subject")
    description: str = Field(..., description="Activity description")
    outcome: str | None = Field(None, description="Activity outcome")
    created_by: str = Field(..., description="User who created the activity")
    occurred_at: datetime = Field(..., description="When the activity occurred")
    next_follow_up: datetime | None = Field(None, description="Next follow-up date")
    is_important: bool = Field(..., description="Whether activity is important")
    created_at: datetime = Field(..., description="Creation timestamp")
    updated_at: datetime = Field(..., description="Last update timestamp")

    model_config = ConfigDict(from_attributes=True)


class ActivityListResponse(BaseModel):
    """Response schema for activity list."""

    items: list[ActivityResponse] = Field(..., description="List of activities")
    total: int = Field(..., description="Total number of activities matching filters")
    page: int = Field(..., description="Current page number")
    limit: int = Field(..., description="Items per page")
    has_more: bool = Field(..., description="Whether there are more items")
