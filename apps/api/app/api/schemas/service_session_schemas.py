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

# Field descriptions the create, update and response models share.
_LOCATION_DESC = "Session location"
_SESSION_TYPE_DESC = "Physical or online"
_CATEGORY_DESC = "Individual / Group / Family / Couples"
_RATE_UGX_DESC = "Per-session rate in UGX"
_APPROVED_BY_DESC = "User ID of approver"
_HEADCOUNT_DESC = "Participant count (group sessions)"

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
    follow_up_of_session_id: str | None = Field(
        None,
        description=(
            "The session this one was booked off the back of, when a counsellor "
            "said the person would be back. A scheduling fact, not a clinical one."
        ),
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
    location: OptionalSanitizedStr = Field(None, description=_LOCATION_DESC)

    # Care Activity Log fields
    session_type: SessionType | None = Field(None, description=_SESSION_TYPE_DESC)
    category: SessionCategory | None = Field(None, description=_CATEGORY_DESC)
    rate_ugx: int | None = Field(None, ge=0, description=_RATE_UGX_DESC)
    issue_topic: OptionalSanitizedStr = Field(None, description="Presenting issue for this session")
    diagnosis_type_id: str | None = Field(None, description="DiagnosisType reference ID")
    diagnosis_id: str | None = Field(None, description="Diagnosis reference ID")
    approved_by: str | None = Field(None, description=_APPROVED_BY_DESC)
    partner_name: OptionalSanitizedStr = Field(
        None, description="Partner name (couples/family sessions)"
    )
    partner_relationship: OptionalSanitizedStr = Field(
        None, description="Partner's relationship to client"
    )
    headcount: int | None = Field(None, ge=2, description=_HEADCOUNT_DESC)
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

    location: OptionalSanitizedStr = Field(None, description=_LOCATION_DESC)
    notes: OptionalSanitizedStr = Field(None, description="Session notes")

    # Care Activity Log fields
    session_type: SessionType | None = Field(None, description=_SESSION_TYPE_DESC)
    category: SessionCategory | None = Field(None, description=_CATEGORY_DESC)
    rate_ugx: int | None = Field(None, ge=0, description=_RATE_UGX_DESC)
    issue_topic: OptionalSanitizedStr = Field(None, description="Presenting issue for this session")
    diagnosis_type_id: str | None = Field(None, description="DiagnosisType reference ID")
    diagnosis_id: str | None = Field(None, description="Diagnosis reference ID")
    approved_by: str | None = Field(None, description=_APPROVED_BY_DESC)
    partner_name: OptionalSanitizedStr = Field(
        None, description="Partner name (couples/family sessions)"
    )
    partner_relationship: OptionalSanitizedStr = Field(
        None, description="Partner's relationship to client"
    )
    headcount: int | None = Field(None, ge=2, description=_HEADCOUNT_DESC)
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
    follow_up_of_session_id: str | None = Field(
        None, description="The session this one was booked off the back of"
    )
    service_id: str = Field(..., description="Service identifier")
    provider_id: str = Field(..., description="Provider (person) identifier")
    attendance: SessionAttendance = Field(..., description="Individual or CompanyWide")
    member_id: str | None = Field(None, description="Absent on a company-wide session")
    client_id: str = Field(..., description="The client the session is attributed to")
    contract_id: str | None = Field(
        None, description="The contract term this session was delivered under, if any"
    )
    # Display names, resolved in bulk so the UI does not fetch one member per
    # row. Absent means unresolved, not nameless.
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
    location: str | None = Field(None, description=_LOCATION_DESC)
    notes: str | None = Field(
        None, description="Session notes. Null if absent or if the caller lacks clinical scope."
    )
    feedback: str | None = Field(
        None, description="Session feedback. Null if absent or if the caller lacks clinical scope."
    )
    cancellation_reason: str | None = Field(None, description="Cancellation reason")
    is_active: bool = Field(..., description="Whether session is active")

    # Care Activity Log fields
    session_type: SessionType | None = Field(None, description=_SESSION_TYPE_DESC)
    category: SessionCategory | None = Field(None, description=_CATEGORY_DESC)
    rate_ugx: int | None = Field(None, description=_RATE_UGX_DESC)
    issue_topic: str | None = Field(
        None, description="Presenting issue. Null if absent or if the caller lacks clinical scope."
    )
    diagnosis_type_id: str | None = Field(
        None, description="DiagnosisType reference ID. Null if absent or lacking clinical scope."
    )
    diagnosis_id: str | None = Field(
        None, description="Diagnosis reference ID. Null if absent or lacking clinical scope."
    )
    approved_by: str | None = Field(None, description=_APPROVED_BY_DESC)
    session_number: int | None = Field(None, description="Ordinal session number for this client")
    partner_name: str | None = Field(
        None, description="Partner name. Null if absent or if the caller lacks clinical scope."
    )
    partner_relationship: str | None = Field(
        None, description="Partner's relationship. Null if absent or lacking clinical scope."
    )
    headcount: int | None = Field(None, description=_HEADCOUNT_DESC)
    client_type: ClientType | None = Field(None, description="New or repeat client")
    clinical_outcome: SessionClinicalStatus | None = Field(
        None, description="Clinical continuation outcome. Null if absent or lacking clinical scope."
    )

    model_config = ConfigDict(from_attributes=True)


class PractitionerAvailability(BaseModel):
    """Whether one practitioner is already spoken for at a given time."""

    provider_id: str
    available: bool = Field(
        ..., description="False when a live booking of theirs overlaps the span"
    )
    clashing_session_id: str | None = Field(
        None, description="The booking in the way, when there is one"
    )
    clashing_scheduled_at: datetime | None = Field(None, description="When that booking starts")


class AvailabilityResponse(BaseModel):
    """What a scheduler needs to pick someone who is free.

    Reports only what it checked: whether each practitioner already has a
    booking in this system overlapping the span. It is not a claim about their
    own diary, which the platform cannot see for an externally affiliated
    practitioner. See "Decision 6" in docs/design/REALTIME_SESSION_CAPTURE.md.
    """

    starts_at: datetime
    ends_at: datetime
    assumed_minutes: int = Field(
        ...,
        description=(
            "The length the span was built from: the service's own duration "
            "where it has one, otherwise the nominal hour. A booking records "
            "no length of its own until it is completed."
        ),
    )
    items: list[PractitionerAvailability]


class SessionChainResponse(BaseModel):
    """One session's place in the chain of care around it.

    One hop each way. A chain is walked a step at a time because there is no
    container holding the whole episode: a case would be that container, and a
    session may not reach one.
    """

    previous: ServiceSessionResponse | None = Field(
        None, description="The session this one was booked off the back of"
    )
    following: list[ServiceSessionResponse] = Field(
        default_factory=list, description="Sessions booked off the back of this one"
    )


class ServiceSessionListResponse(BaseModel):
    """Response schema for service session list."""

    items: list[ServiceSessionResponse] = Field(..., description="List of sessions")
    total: int = Field(..., description="Total number of sessions matching filters")
    page: int = Field(..., description="Current page number")
    limit: int = Field(..., description="Items per page")
    has_more: bool = Field(..., description="Whether there are more items")
