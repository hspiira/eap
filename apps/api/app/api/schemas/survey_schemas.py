"""Survey API schemas (Phase 3 #D-Survey)."""

from datetime import date, datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from app.api.schemas.base import SanitizedStr
from app.domain.enums import SurveyCampaignStatus


class ApprovedQuestionInput(BaseModel):
    """A question whose answers may be counted in an employer-facing aggregate.

    Aggregates report these questions and these choices only, so free text
    stays out of every employer-facing surface.
    """

    key: SanitizedStr = Field(..., min_length=1, max_length=255)
    label: SanitizedStr = Field(..., min_length=1, max_length=255)
    choices: list[SanitizedStr] = Field(..., min_length=1, max_length=50)


class SurveyCampaignCreate(BaseModel):
    client_id: str
    name: SanitizedStr = Field(..., min_length=1, max_length=255)
    source: str
    external_form_id: SanitizedStr = Field(..., min_length=1, max_length=255)
    webhook_secret: str = Field(..., min_length=32, max_length=255)
    period_start: date | None = None
    period_end: date | None = None
    anonymous: bool = True
    approved_questions: list[ApprovedQuestionInput] = Field(default_factory=list)


class SurveyCampaignResponse(BaseModel):
    id: str
    tenant_id: str
    client_id: str
    name: str
    source: str
    external_form_id: str
    status: SurveyCampaignStatus
    period_start: date | None
    period_end: date | None
    anonymous: bool
    approved_questions: list[ApprovedQuestionInput]
    response_count: int
    created_by: str
    activated_at: datetime | None
    closed_at: datetime | None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class SurveyCampaignListResponse(BaseModel):
    items: list[SurveyCampaignResponse]
    total: int
    page: int
    limit: int
    has_more: bool


class SurveyResponseAcceptedResponse(BaseModel):
    """Returned by the webhook endpoint."""

    response_id: str
    accepted: bool
    duplicate: bool


class SurveyAggregateResponse(BaseModel):
    """Employer-facing aggregate: approved questions only, every cell suppressed.

    A count below ``min_cell_size`` is returned as the ``"<n"`` token rather
    than a number, including ``response_total``.
    """

    campaign_id: str
    client_id: str
    name: str
    status: SurveyCampaignStatus
    source: str
    anonymous: bool
    disclosure_status: str
    question_labels: dict[str, str]
    answer_frequencies: dict[str, dict[str, int | str]]
    unapproved_answers: dict[str, int | str]
    response_total: int | str
    min_cell_size: int
    generated_at: str


class WebhookPayload(BaseModel):
    """Generic provider-agnostic shape; raw provider payload arrives in ``answers``."""

    external_response_id: str = Field(..., min_length=1)
    submitted_at: datetime
    answers: dict[str, Any]
    metrics: dict[str, Any] | None = None
