"""Survey API schemas (Phase 3 #D-Survey)."""

from datetime import date, datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from app.api.schemas.base import SanitizedStr
from app.domain.enums import SurveyCampaignStatus, SurveySource


class SurveyCampaignCreate(BaseModel):
    client_id: str
    name: SanitizedStr = Field(..., min_length=1, max_length=255)
    source: SurveySource
    external_form_id: SanitizedStr = Field(..., min_length=1, max_length=255)
    webhook_secret: str = Field(..., min_length=32, max_length=255)
    period_start: date | None = None
    period_end: date | None = None
    anonymous: bool = True


class SurveyCampaignResponse(BaseModel):
    id: str
    tenant_id: str
    client_id: str
    name: str
    source: SurveySource
    external_form_id: str
    status: SurveyCampaignStatus
    period_start: date | None
    period_end: date | None
    anonymous: bool
    response_count: int
    created_by: str
    activated_at: datetime | None
    closed_at: datetime | None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class SurveyResponseAcceptedResponse(BaseModel):
    """Returned by the webhook endpoint."""

    response_id: str
    accepted: bool
    duplicate: bool


class SurveyAggregateResponse(BaseModel):
    campaign_id: str
    client_id: str
    name: str
    status: SurveyCampaignStatus
    source: SurveySource
    anonymous: bool
    response_total: int
    answer_frequencies: dict[str, dict[str, int]]
    generated_at: str


class WebhookPayload(BaseModel):
    """Generic provider-agnostic shape; raw provider payload arrives in ``answers``."""

    external_response_id: str = Field(..., min_length=1)
    submitted_at: datetime
    answers: dict[str, Any]
    metrics: dict[str, Any] | None = None
