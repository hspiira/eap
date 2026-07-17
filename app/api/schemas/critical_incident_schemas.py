"""Critical Incident API schemas (Phase 2 #D-CISM)."""

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from app.api.schemas.base import OptionalSanitizedStr, SanitizedStr
from app.domain.enums import (
    CriticalIncidentPhase,
    CriticalIncidentSeverity,
    CriticalIncidentStatus,
)


class CriticalIncidentCreate(BaseModel):
    client_id: str = Field(..., description="Client identifier")
    event_description: SanitizedStr = Field(..., min_length=1, description="What happened")
    severity: CriticalIncidentSeverity = Field(..., description="Operational severity")
    affected_population_size: int = Field(..., ge=0, description="Headcount affected")
    occurred_at: datetime = Field(..., description="When the event occurred (UTC)")


class IncidentPhaseRecord(BaseModel):
    phase: CriticalIncidentPhase = Field(..., description="CISM phase")
    notes: OptionalSanitizedStr = Field(None, description="Notes for this phase")


class IncidentClose(BaseModel):
    after_action_summary: SanitizedStr = Field(
        ..., min_length=1, description="After-action summary"
    )


class IncidentPhaseEntryResponse(BaseModel):
    phase: CriticalIncidentPhase
    occurred_at: datetime
    notes: str | None = None


class CriticalIncidentResponse(BaseModel):
    id: str
    tenant_id: str
    client_id: str
    event_description: str
    severity: CriticalIncidentSeverity
    affected_population_size: int
    occurred_at: datetime
    logged_by: str
    status: CriticalIncidentStatus
    phases: list[IncidentPhaseEntryResponse]
    after_action_summary: str | None
    closed_at: datetime | None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class CriticalIncidentListResponse(BaseModel):
    items: list[CriticalIncidentResponse]
    total: int
