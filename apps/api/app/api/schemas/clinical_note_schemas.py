"""Clinical note API schemas."""

from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from app.api.schemas.base import SanitizedStr
from app.domain.enums import ClinicalNoteType


class CreateClinicalNoteRequest(BaseModel):
    case_id: str
    note_type: ClinicalNoteType
    body: dict[str, Any] = Field(..., min_length=1)
    session_id: str | None = None


class UpdateClinicalNoteBodyRequest(BaseModel):
    body: dict[str, Any] = Field(..., min_length=1)


class AmendClinicalNoteRequest(BaseModel):
    body: dict[str, Any] = Field(..., min_length=1)
    reason: SanitizedStr = Field(..., min_length=1, max_length=500)


class NoteAmendmentResponse(BaseModel):
    id: str
    author_id: str
    body: dict[str, Any]
    reason: str
    created_at: datetime


class ClinicalNoteResponse(BaseModel):
    id: str
    tenant_id: str
    case_id: str
    clinical_subject_id: str
    note_type: ClinicalNoteType
    body: dict[str, Any]
    author_id: str
    session_id: str | None
    signed_at: datetime | None
    signed_by: str | None
    locked_at: datetime | None
    amendments: list[NoteAmendmentResponse]
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
