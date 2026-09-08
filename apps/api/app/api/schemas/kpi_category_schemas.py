"""KPI category taxonomy API schemas."""

from pydantic import BaseModel, ConfigDict, Field


class KPICategoryResponse(BaseModel):
    id: str = Field(..., description="KPI category identifier")
    code: str = Field(..., description="Stable category code")
    name: str = Field(..., description="Display name")
    description: str | None = Field(None, description="Optional description")
    sort_order: int = Field(..., description="Sort order")

    model_config = ConfigDict(from_attributes=True)


class KPICategoryCreate(BaseModel):
    code: str = Field(..., min_length=1, max_length=50, description="Stable category code")
    name: str = Field(..., min_length=1, max_length=255, description="Display name")
    description: str | None = Field(None, description="Optional description")
    sort_order: int = Field(0, description="Sort order")


class KPICategoryUpdate(BaseModel):
    name: str | None = Field(None, min_length=1, max_length=255)
    description: str | None = None
    sort_order: int | None = None
