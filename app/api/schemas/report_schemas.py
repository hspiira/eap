"""Report API schemas (Phase 2 #D-Reports)."""

from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from app.api.schemas.base import OptionalSanitizedStr, SanitizedStr
from app.domain.enums import ReportQueryType, ReportRunStatus


class TemplateSectionInput(BaseModel):
    title: SanitizedStr = Field(..., min_length=1, description="Section heading")
    query_type: ReportQueryType = Field(..., description="Query to run")
    parameters: dict[str, Any] = Field(default_factory=dict)
    narrative: OptionalSanitizedStr = Field(None)


class ReportTemplateCreate(BaseModel):
    code: SanitizedStr = Field(..., min_length=1, description="Stable code, unique per tenant")
    name: SanitizedStr = Field(..., min_length=1)
    description: OptionalSanitizedStr = None
    sections: list[TemplateSectionInput] = Field(..., min_length=1)


class ReportTemplateResponse(BaseModel):
    id: str
    tenant_id: str
    code: str
    name: str
    description: str | None
    sections: list[TemplateSectionInput]
    is_active: bool
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class ReportRunRequest(BaseModel):
    parameters: dict[str, Any] = Field(default_factory=dict)


class ReportRunResponse(BaseModel):
    id: str
    tenant_id: str
    template_id: str
    requested_by: str
    parameters: dict[str, Any]
    status: ReportRunStatus
    started_at: datetime | None
    completed_at: datetime | None
    output: dict[str, Any] | None
    error: str | None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
