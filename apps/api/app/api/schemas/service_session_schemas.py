"""
Service Session API Schemas (DTOs)

Pydantic models for request/response validation.
Separate from domain entities.
"""

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, model_validator

from app.api.schemas.base import OptionalSanitizedStr, SanitizedStr
from app.domain.enums import (
    ClientType,
    SessionAttendance,
    SessionCategory,
    SessionClinicalStatus,
    SessionDeliveryContext,
    SessionStatus,
    SessionType,
)

# === Request Schemas ===


class ServiceSessionCreate(BaseModel):
    """Request schema for creating a service session."""

    service_id: str = Field(..., description="Service identifier")
    provider_id: str = Field(..., description="Provider (person) identifier")
    attendance: SessionAttendance = Field(
        SessionAttendance.INDIVIDUAL,
        description="Individual names a member; CompanyWide names a client and a headcount",
    )
    member_id: str | None = Field(
        None, description="Required for an Individual session, forbidden for a CompanyWide one"
    )
    client_id: str | None = Field(
        None,
        description=(
            "Required for a CompanyWide session. For an Individual session it is taken "
            "from the member, so that the two cannot disagree"
        ),
    )
    scheduled_at: datetime = Field(..., description="Scheduled date and time")
    delivery_context: SessionDeliveryContext = Field(
        ...,
        description="Direct or Organisation. Unknown is rejected: it belongs to historical import",
    )
    provider_affiliation_id: str | None = Field(
        None, description="Required for Organisation delivery, forbidden otherwise"
    )
    location: OptionalSanitizedStr = Field(None, description="Session location")

    # Care Activity Log fields
    session_type: SessionType | None = Field(None, description="Physical or online")
    category: SessionCategory | None = Field(
        None, description="Individual / Group / Family / Couples"
    )
    rate_ugx: int | None = Field(None, ge=0, description="Per-session rate in UGX")
    issue_topic: OptionalSanitizedStr = Field(None, description="Presenting issue for this session")
    diagnosis_type_id: str | None = Field(None, description="DiagnosisType reference ID")
    diagnosis_id: str | None = Field(None, description="Diagnosis reference ID")
    approved_by: str | None = Field(None, description="User ID of approver")
    session_number: int | None = Field(
        None, ge=1, description="Ordinal session number for this client"
    )
    partner_name: OptionalSanitizedStr = Field(
        None, description="Partner name (couples/family sessions)"
    )
    partner_relationship: OptionalSanitizedStr = Field(
        None, description="Partner's relationship to client"
    )
    headcount: int | None = Field(None, ge=2, description="Participant count (group sessions)")
    client_type: ClientType | None = Field(None, description="New or repeat client")
    clinical_outcome: SessionClinicalStatus | None = Field(
        None, description="Clinical continuation outcome"
    )

    @model_validator(mode="after")
    def validate_attendance(self) -> "ServiceSessionCreate":
        """A health talk names a client and a headcount; a session names a member.

        Rejecting rather than defaulting matters here: a CompanyWide session
        that silently accepted a member would be indistinguishable from an
        individual one, and the headcount is the only measure of group reach.
        """
        if self.attendance is SessionAttendance.COMPANY_WIDE:
            if self.member_id:
                raise ValueError("A company-wide session cannot name a member")
            if not self.client_id:
                raise ValueError("A company-wide session requires a client")
            if self.headcount is None:
                raise ValueError("A company-wide session requires a headcount")
            return self
        if not self.member_id:
            raise ValueError("An individual session requires a member")
        return self


class ServiceSessionCompleteRequest(BaseModel):
    """Request schema for completing a session."""

    duration: int = Field(..., gt=0, description="Session duration in minutes")
    notes: SanitizedStr = Field(..., min_length=1, description="Session notes")
    case_id: str | None = Field(
        None,
        description=(
            "Clinical case to draw this session down against. Supplied by a caller that "
            "already holds clinical context; it cannot be inferred from the session, "
            "which carries an employer-side member id. Omit to leave the authorization "
            "untouched and consume it through the manual route."
        ),
    )


class ServiceSessionCompleteResponse(BaseModel):
    """A completed session and what the completion did to the authorization."""

    session: "ServiceSessionResponse"
    drawdown: "SessionDrawdownResponse"


class SessionDrawdownResponse(BaseModel):
    """What the completion did, or did not do, to the programme authorization."""

    consumed: bool = Field(..., description="Whether a session was drawn down")
    authorization_id: str | None = Field(None, description="Authorization consumed, if any")
    sessions_remaining: int | None = Field(None, description="Remaining after the drawdown")
    reason: str | None = Field(None, description="Why no drawdown happened")


class ServiceSessionCancelRequest(BaseModel):
    """Request schema for cancelling a session."""

    reason: SanitizedStr = Field(..., min_length=1, description="Cancellation reason")


class ServiceSessionRescheduleRequest(BaseModel):
    """Request schema for rescheduling a session."""

    new_scheduled_at: datetime = Field(..., description="New scheduled date and time")


class ServiceSessionUpdate(BaseModel):
    """Request schema for updating session information."""

    location: OptionalSanitizedStr = Field(None, description="Session location")
    notes: OptionalSanitizedStr = Field(None, description="Session notes")

    # Care Activity Log fields
    session_type: SessionType | None = Field(None, description="Physical or online")
    category: SessionCategory | None = Field(
        None, description="Individual / Group / Family / Couples"
    )
    rate_ugx: int | None = Field(None, ge=0, description="Per-session rate in UGX")
    issue_topic: OptionalSanitizedStr = Field(None, description="Presenting issue for this session")
    diagnosis_type_id: str | None = Field(None, description="DiagnosisType reference ID")
    diagnosis_id: str | None = Field(None, description="Diagnosis reference ID")
    approved_by: str | None = Field(None, description="User ID of approver")
    partner_name: OptionalSanitizedStr = Field(
        None, description="Partner name (couples/family sessions)"
    )
    partner_relationship: OptionalSanitizedStr = Field(
        None, description="Partner's relationship to client"
    )
    headcount: int | None = Field(None, ge=2, description="Participant count (group sessions)")
    client_type: ClientType | None = Field(None, description="New or repeat client")
    clinical_outcome: SessionClinicalStatus | None = Field(
        None, description="Clinical continuation outcome"
    )

    @model_validator(mode="after")
    def _validate_at_least_one_field(self) -> "ServiceSessionUpdate":
        if not any(v is not None for v in self.model_dump().values()):
            raise ValueError("At least one field must be provided for update")
        return self


class ServiceSessionUpdateFeedback(BaseModel):
    """Request schema for updating session feedback."""

    feedback: SanitizedStr = Field(..., min_length=1, description="Session feedback")


# === Response Schemas ===


class ServiceSessionResponse(BaseModel):
    """Response schema for service session."""

    id: str = Field(..., description="Session identifier")
    tenant_id: str = Field(..., description="Tenant identifier")
    service_id: str = Field(..., description="Service identifier")
    provider_id: str = Field(..., description="Provider (person) identifier")
    attendance: SessionAttendance = Field(..., description="Individual or CompanyWide")
    member_id: str | None = Field(None, description="Absent on a company-wide session")
    client_id: str = Field(..., description="The client the session is attributed to")
    contract_id: str | None = Field(
        None, description="The contract term this session was delivered under, if any"
    )
    # Display names, resolved in bulk on the list path so the UI does not fetch
    # one member per row. Absent means unresolved, not nameless.
    client_name: str | None = Field(None, description="Resolved client name")
    member_display_label: str | None = Field(None, description="Resolved member name")
    provider_display_name: str | None = Field(None, description="Resolved practitioner name")
    service_name: str | None = Field(None, description="Resolved service name")
    scheduled_at: datetime = Field(..., description="Scheduled date and time")
    delivery_context: SessionDeliveryContext = Field(..., description="How this was delivered")
    provider_affiliation_id: str | None = Field(
        None, description="The affiliation this session is attributed to, if any"
    )
    provider_organisation_id: str | None = Field(
        None,
        description=(
            "Resolved from this session's own affiliation, never from the "
            "practitioner's current affiliations"
        ),
    )
    status: SessionStatus = Field(..., description="Session status")
    reschedule_count: int = Field(..., description="Number of times rescheduled")
    completed_at: datetime | None = Field(None, description="Completion date and time")
    duration: int | None = Field(None, description="Session duration in minutes")
    location: str | None = Field(None, description="Session location")
    notes: str | None = Field(None, description="Session notes")
    feedback: str | None = Field(None, description="Session feedback")
    cancellation_reason: str | None = Field(None, description="Cancellation reason")
    is_active: bool = Field(..., description="Whether session is active")

    # Care Activity Log fields
    session_type: SessionType | None = Field(None, description="Physical or online")
    category: SessionCategory | None = Field(
        None, description="Individual / Group / Family / Couples"
    )
    rate_ugx: int | None = Field(None, description="Per-session rate in UGX")
    issue_topic: str | None = Field(None, description="Presenting issue for this session")
    diagnosis_type_id: str | None = Field(None, description="DiagnosisType reference ID")
    diagnosis_id: str | None = Field(None, description="Diagnosis reference ID")
    approved_by: str | None = Field(None, description="User ID of approver")
    session_number: int | None = Field(None, description="Ordinal session number for this client")
    partner_name: str | None = Field(None, description="Partner name (couples/family sessions)")
    partner_relationship: str | None = Field(None, description="Partner's relationship to client")
    headcount: int | None = Field(None, description="Participant count (group sessions)")
    client_type: ClientType | None = Field(None, description="New or repeat client")
    clinical_outcome: SessionClinicalStatus | None = Field(
        None, description="Clinical continuation outcome"
    )

    model_config = ConfigDict(from_attributes=True)


class ServiceSessionListResponse(BaseModel):
    """Response schema for service session list."""

    items: list[ServiceSessionResponse] = Field(..., description="List of sessions")
    total: int = Field(..., description="Total number of sessions matching filters")
    page: int = Field(..., description="Current page number")
    limit: int = Field(..., description="Items per page")
    has_more: bool = Field(..., description="Whether there are more items")
