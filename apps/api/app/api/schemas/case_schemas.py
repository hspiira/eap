"""Clinical case API schemas."""

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from app.api.schemas.base import OptionalSanitizedStr, SanitizedStr
from app.domain.enums import (
    CaseClosureReason,
    CaseStatus,
)


class OpenCaseRequest(BaseModel):
    client_id: str
    member_id: str
    presenting_problem: str
    referral_source: str
    referral_notes: OptionalSanitizedStr = None


class AssignCounsellorRequest(BaseModel):
    counsellor_id: str


class AdvanceCaseRequest(BaseModel):
    target: CaseStatus


class CloseCaseRequest(BaseModel):
    reason: CaseClosureReason
    closure_summary_note_id: OptionalSanitizedStr = None


class ReferOutCaseRequest(BaseModel):
    notes: SanitizedStr = Field(..., min_length=1)


class CaseResponse(BaseModel):
    id: str
    tenant_id: str
    clinical_subject_id: str
    client_id: str
    presenting_problem: str
    referral_source: str
    status: CaseStatus
    opened_at: datetime
    assigned_counsellor_id: str | None
    authorization_id: str | None
    referred_by_user_id: str | None
    referral_notes: str | None
    closed_at: datetime | None
    closure_reason: CaseClosureReason | None
    closure_summary_note_id: str | None
    intake_screener_admin_ids: list[str]
    closure_screener_admin_ids: list[str]
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
