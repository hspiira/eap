"""Presenting problem taxonomy API schemas."""

from pydantic import BaseModel, ConfigDict, Field


class PresentingProblemResponse(BaseModel):
    id: str = Field(..., description="Presenting problem identifier")
    code: str = Field(..., description="Stable code")
    name: str = Field(..., description="Display name")
    description: str | None = Field(None, description="Optional description")
    sort_order: int = Field(..., description="Sort order")

    model_config = ConfigDict(from_attributes=True)


class PresentingProblemCreate(BaseModel):
    code: str = Field(..., min_length=1, max_length=50, description="Stable code")
    name: str = Field(..., min_length=1, max_length=255, description="Display name")
    description: str | None = Field(None, description="Optional description")
    sort_order: int = Field(0, description="Sort order")


class PresentingProblemUpdate(BaseModel):
    name: str | None = Field(None, min_length=1, max_length=255)
    description: str | None = None
    sort_order: int | None = None
