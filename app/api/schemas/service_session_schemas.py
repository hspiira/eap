"""
Service Session API Schemas (DTOs)

Pydantic models for request/response validation.
Separate from domain entities.
"""

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from app.domain.enums import SessionStatus


# === Request Schemas ===

class ServiceSessionCreate(BaseModel):
    """Request schema for creating a service session."""

    service_id: str = Field(..., description="Service identifier")
    provider_id: str = Field(..., description="Provider (person) identifier")
    person_id: str = Field(..., description="Person identifier")
    scheduled_at: datetime = Field(..., description="Scheduled date and time")
    location: str | None = Field(None, description="Session location")


class ServiceSessionCompleteRequest(BaseModel):
    """Request schema for completing a session."""

    duration: int = Field(..., gt=0, description="Session duration in minutes")
    notes: str = Field(..., min_length=1, description="Session notes")


class ServiceSessionCancelRequest(BaseModel):
    """Request schema for cancelling a session."""

    reason: str = Field(..., min_length=1, description="Cancellation reason")


class ServiceSessionRescheduleRequest(BaseModel):
    """Request schema for rescheduling a session."""

    new_scheduled_at: datetime = Field(..., description="New scheduled date and time")


class ServiceSessionUpdate(BaseModel):
    """Request schema for updating session information."""

    location: str | None = Field(None, description="Session location")
    notes: str | None = Field(None, description="Session notes")


class ServiceSessionUpdateFeedback(BaseModel):
    """Request schema for updating session feedback."""

    feedback: str = Field(..., min_length=1, description="Session feedback")


# === Response Schemas ===

class ServiceSessionResponse(BaseModel):
    """Response schema for service session."""

    id: str = Field(..., description="Session identifier")
    tenant_id: str = Field(..., description="Tenant identifier")
    service_id: str = Field(..., description="Service identifier")
    provider_id: str = Field(..., description="Provider (person) identifier")
    person_id: str = Field(..., description="Person identifier")
    scheduled_at: datetime = Field(..., description="Scheduled date and time")
    status: SessionStatus = Field(..., description="Session status")
    reschedule_count: int = Field(..., description="Number of times rescheduled")
    completed_at: datetime | None = Field(None, description="Completion date and time")
    duration: int | None = Field(None, description="Session duration in minutes")
    location: str | None = Field(None, description="Session location")
    notes: str | None = Field(None, description="Session notes")
    feedback: str | None = Field(None, description="Session feedback")
    cancellation_reason: str | None = Field(None, description="Cancellation reason")
    is_active: bool = Field(..., description="Whether session is active")

    model_config = ConfigDict(from_attributes=True)


class ServiceSessionListResponse(BaseModel):
    """Response schema for service session list."""

    items: list[ServiceSessionResponse] = Field(..., description="List of sessions")
    total: int = Field(..., description="Total number of sessions matching filters")
    page: int = Field(..., description="Current page number")
    limit: int = Field(..., description="Items per page")
    has_more: bool = Field(..., description="Whether there are more items")
