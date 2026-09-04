"""Care Callback API schemas (Phase 3 #D-CareCallback)."""

from datetime import date, datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from app.api.schemas.base import OptionalSanitizedStr, SanitizedStr
from app.domain.enums import (
    CareCallbackCampaignStatus,
    OutreachStatus,
    StageOfChange,
    TriageInstrumentCode,
    TriageRiskLevel,
)


class CareCallbackCampaignCreate(BaseModel):
    client_id: str = Field(..., description="Client identifier")
    name: SanitizedStr = Field(..., min_length=1, max_length=255)
    period_start: date
    period_end: date
    target_count: int = Field(..., ge=0)
    counsellor_pool: list[str] = Field(
        ..., min_length=1, description="Person IDs of counsellors on this campaign"
    )
    sampling_notes: OptionalSanitizedStr = None


class CounsellorPoolUpdate(BaseModel):
    counsellor_pool: list[str] = Field(..., min_length=1)


class EnrolPersonsRequest(BaseModel):
    person_ids: list[str] = Field(..., min_length=1)


class OutreachAssignRequest(BaseModel):
    counsellor_id: str


class TriageRecordRequest(BaseModel):
    instrument_code: str = Field(..., min_length=1)
    responses: dict[str, Any]
    scores: dict[str, Any]
    risk_level: TriageRiskLevel
    crisis_flag: bool = False
    crisis_reason: OptionalSanitizedStr = None


class TriageScoreRequest(BaseModel):
    """Server-side scoring path: raw Likert answers → scored + recorded triage."""

    instrument_code: TriageInstrumentCode
    responses: dict[str, int] = Field(..., description="Item code → integer Likert answer")


class TriageItemSchema(BaseModel):
    code: str
    text: str
    min_value: int
    max_value: int


class TriageInstrumentSchema(BaseModel):
    code: TriageInstrumentCode
    version: str
    title: str
    items: list[TriageItemSchema]


class TriageScoreResponse(BaseModel):
    """Computed triage classification, returned alongside the persisted outreach record."""

    instrument_code: TriageInstrumentCode
    instrument_version: str
    risk_level: TriageRiskLevel
    crisis_flag: bool
    crisis_reason: str | None
    scores: dict[str, Any]
    derived: dict[str, Any]
    stage_of_change: StageOfChange | None = None


class OutreachTerminate(BaseModel):
    notes: OptionalSanitizedStr = None


class OutreachEscalate(BaseModel):
    notes: SanitizedStr = Field(..., min_length=1)


class CareCallbackCampaignResponse(BaseModel):
    id: str
    tenant_id: str
    client_id: str
    name: str
    period_start: date
    period_end: date
    target_count: int
    completed_count: int
    counsellor_pool: list[str]
    status: CareCallbackCampaignStatus
    sampling_notes: str | None
    created_by: str
    activated_at: datetime | None
    completed_at: datetime | None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class OutreachRecordResponse(BaseModel):
    id: str
    tenant_id: str
    campaign_id: str
    person_id: str
    counsellor_id: str | None
    status: OutreachStatus
    contact_attempts: int
    assigned_at: datetime | None
    last_attempted_at: datetime | None
    completed_at: datetime | None
    triage_instrument_code: str | None
    triage_risk_level: TriageRiskLevel | None
    crisis_flag: bool
    notes: str | None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class CampaignSummaryResponse(BaseModel):
    campaign_id: str
    client_id: str
    name: str
    status: CareCallbackCampaignStatus
    target_count: int
    completed_count: int
    progress_ratio: float
    outreach_total: int
    outreach_by_status: dict[str, int]
    triage_completed: int
    crisis_flags: int
    period_start: str
    period_end: str
    generated_at: str
