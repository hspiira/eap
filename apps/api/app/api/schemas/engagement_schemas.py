"""Engagement API schemas (Phase 4 #D-Engagement)."""

from datetime import date, datetime

from pydantic import BaseModel, ConfigDict, Field

from app.api.schemas.base import OptionalSanitizedStr, SanitizedStr
from app.domain.enums import DeliverableStatus, EngagementStatus


class EngagementCreate(BaseModel):
    client_id: str
    name: SanitizedStr = Field(..., min_length=1, max_length=255)
    description: OptionalSanitizedStr = None
    period_start: date | None = None
    period_end: date | None = None


class DeliverableCreate(BaseModel):
    title: SanitizedStr = Field(..., min_length=1, max_length=255)
    description: OptionalSanitizedStr = None
    due_date: date | None = None


class DeliverableStatusUpdate(BaseModel):
    status: DeliverableStatus


class HoursLogCreate(BaseModel):
    user_id: str
    logged_on: date
    hours: float = Field(..., gt=0, le=24)
    note: OptionalSanitizedStr = None


class DeliverableResponse(BaseModel):
    id: str
    title: str
    description: str | None
    due_date: date | None
    status: DeliverableStatus
    delivered_at: datetime | None

    model_config = ConfigDict(from_attributes=True)


class HoursLogResponse(BaseModel):
    id: str
    user_id: str
    logged_on: date
    hours: float
    note: str | None

    model_config = ConfigDict(from_attributes=True)


class EngagementResponse(BaseModel):
    id: str
    tenant_id: str
    client_id: str
    name: str
    description: str | None
    status: EngagementStatus
    period_start: date | None
    period_end: date | None
    deliverables: list[DeliverableResponse]
    hours_log: list[HoursLogResponse]
    created_by: str
    activated_at: datetime | None
    delivered_at: datetime | None
    invoiced_at: datetime | None
    closed_at: datetime | None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class EngagementSummaryResponse(BaseModel):
    engagement_id: str
    client_id: str
    name: str
    status: EngagementStatus
    deliverable_count: int
    deliverable_mix: dict[str, int]
    total_hours: float
    hours_by_user: dict[str, float]
    period_start: str | None
    period_end: str | None
    generated_at: str
