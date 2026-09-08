"""Utilisation event type taxonomy API schemas."""

from pydantic import BaseModel, ConfigDict, Field


class UtilisationEventTypeResponse(BaseModel):
    id: str = Field(..., description="Utilisation event type identifier")
    code: str = Field(..., description="Stable code")
    name: str = Field(..., description="Display name")
    description: str | None = Field(None, description="Optional description")
    sort_order: int = Field(..., description="Sort order")

    model_config = ConfigDict(from_attributes=True)


class UtilisationEventTypeCreate(BaseModel):
    code: str = Field(..., min_length=1, max_length=50, description="Stable code")
    name: str = Field(..., min_length=1, max_length=255, description="Display name")
    description: str | None = Field(None, description="Optional description")
    sort_order: int = Field(0, description="Sort order")


class UtilisationEventTypeUpdate(BaseModel):
    name: str | None = Field(None, min_length=1, max_length=255)
    description: str | None = None
    sort_order: int | None = None
