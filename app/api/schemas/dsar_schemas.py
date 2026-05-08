"""DSAR API schemas (Phase 4 #DSAR)."""

from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from app.domain.enums import DSARRequestStatus, DSARRequestType


class DSARRequestCreate(BaseModel):
    subject_person_id: str
    reversible_window_days: int | None = Field(
        default=None,
        ge=0,
        description="Override the default reversible window (erasure only)",
    )


class DSARRequestResponse(BaseModel):
    id: str
    tenant_id: str
    subject_person_id: str
    request_type: DSARRequestType
    status: DSARRequestStatus
    requested_by: str
    started_at: datetime | None
    completed_at: datetime | None
    failed_reason: str | None
    erasure_executes_at: datetime | None
    output: dict[str, Any] | None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class RetentionPolicyResponse(BaseModel):
    data_class: str
    days: int
    rationale: str
