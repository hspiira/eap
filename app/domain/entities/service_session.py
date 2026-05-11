"""
Service Session Entity (Aggregate Root)

Represents an individual service delivery session.
"""

from dataclasses import dataclass, field
from datetime import datetime
from app.domain.value_objects.core import SessionId, TenantId, ServiceId, PersonId
from app.domain.enums import SessionStatus, SessionType, SessionCategory, ClientType, SessionClinicalStatus
from app.domain.events import DomainEvent, SessionCompleted, SessionCancelled, SessionRescheduled
from app.domain.exceptions import DomainError
from app.shared.utils.datetime import utc_now

@dataclass
class ServiceSessionEntity:
    # Required fields (no defaults)
    id: SessionId
    tenant_id: TenantId
    service_id: ServiceId
    provider_id: PersonId
    person_id: PersonId
    scheduled_at: datetime
    status: SessionStatus
    created_at: datetime
    updated_at: datetime
    reschedule_count: int
    
    # Optional fields (with defaults)
    completed_at: datetime | None = None
    duration: int | None = None
    location: str | None = None
    notes: str | None = None
    feedback: str | None = None
    cancellation_reason: str | None = None
    incident_id: str | None = None
    deleted_at: datetime | None = None

    # Care Activity Log fields
    session_type: SessionType | None = None          # Physical / Online
    category: SessionCategory | None = None          # Individual / Group / Family / Couples
    rate_ugx: int | None = None                      # Per-session rate in UGX
    issue_topic: str | None = None                   # Presenting issue for this session (encrypted at rest)
    diagnosis_type_id: str | None = None             # Ref to DiagnosisType.id
    diagnosis_id: str | None = None                  # Ref to Diagnosis.id
    approved_by: str | None = None                   # UserId who approved the session
    session_number: int | None = None                # Ordinal session number for this client
    partner_name: str | None = None                  # Couples/family partner (encrypted at rest)
    partner_relationship: str | None = None          # Relationship of partner to primary client
    headcount: int | None = None                     # Participant count for group sessions
    client_type: ClientType | None = None            # New / Repeat
    clinical_outcome: SessionClinicalStatus | None = None  # ToBeContinued / Referred / Completed

    events: list[DomainEvent] = field(default_factory=list[DomainEvent])
    
    def complete(self, duration: int, notes: str | None = None) -> None:
        if self.status not in {SessionStatus.SCHEDULED, SessionStatus.RESCHEDULED}:
            raise DomainError("Only scheduled sessions can be completed")
        if duration <= 0:
            raise DomainError("Duration must be positive")
        if not notes:
            raise DomainError("Notes are required for completed session")
        self.status = SessionStatus.COMPLETED
        self.completed_at = utc_now()
        self.duration = duration
        self.notes = notes
        self.events.append(SessionCompleted(occurred_at=utc_now(), session_id=self.id, person_id=self.person_id))
    
    def cancel(self, reason: str) -> None:
        """Cancel a session"""
        if self.deleted_at:
            raise DomainError("Cannot cancel deleted session")
        if self.status in {SessionStatus.COMPLETED, SessionStatus.CANCELLED, SessionStatus.NO_SHOW}:
            raise DomainError("Cannot cancel completed or finalized session")
        if not reason:
            raise DomainError("Cancellation requires reason")
        self.status = SessionStatus.CANCELLED
        self.cancellation_reason = reason
        self.updated_at = utc_now()
        self.events.append(SessionCancelled(occurred_at=utc_now(), session_id=self.id, reason=reason))
    
    def reschedule(self, new_scheduled_at: datetime) -> None:
        """Reschedule a session"""
        if self.deleted_at:
            raise DomainError("Cannot reschedule deleted session")
        if self.status in {SessionStatus.COMPLETED, SessionStatus.CANCELLED, SessionStatus.NO_SHOW}:
            raise DomainError("Cannot reschedule completed or finalized session")
        if new_scheduled_at <= utc_now():
            raise DomainError("New scheduled time must be in the future")
        self.status = SessionStatus.RESCHEDULED
        self.scheduled_at = new_scheduled_at
        self.reschedule_count += 1
        self.updated_at = utc_now()
        self.events.append(SessionRescheduled(occurred_at=utc_now(), session_id=self.id, new_scheduled_at=new_scheduled_at))
    
    def mark_no_show(self) -> None:
        """Mark a session as no-show"""
        if self.deleted_at:
            raise DomainError("Cannot mark deleted session as no-show")
        if self.status in {SessionStatus.COMPLETED, SessionStatus.CANCELLED, SessionStatus.NO_SHOW}:
            raise DomainError("Cannot mark completed or finalized session as no-show")
        self.status = SessionStatus.NO_SHOW
        self.updated_at = utc_now()
    
    def update_location(self, location: str | None) -> None:
        """Update session location"""
        if self.deleted_at:
            raise DomainError("Cannot update location for deleted session")
        if self.status in {SessionStatus.COMPLETED, SessionStatus.CANCELLED}:
            raise DomainError("Cannot update location for completed or cancelled session")
        self.location = location
        self.updated_at = utc_now()
    
    def update_notes(self, notes: str | None) -> None:
        """Update session notes"""
        if self.deleted_at:
            raise DomainError("Cannot update notes for deleted session")
        self.notes = notes
        self.updated_at = utc_now()
    
    def update_feedback(self, feedback: str | None) -> None:
        """Update session feedback"""
        if self.deleted_at:
            raise DomainError("Cannot update feedback for deleted session")
        if self.status != SessionStatus.COMPLETED:
            raise DomainError("Feedback can only be added to completed sessions")
        self.feedback = feedback
        self.updated_at = utc_now()
    
    def archive(self) -> None:
        """Archive a session"""
        if self.deleted_at:
            raise DomainError("Cannot archive deleted session")
        # Archive is a soft delete operation
        self.deleted_at = utc_now()
        self.updated_at = utc_now()
    
    def restore(self) -> None:
        """Restore an archived session"""
        if not self.deleted_at:
            raise DomainError("Session is not archived and does not need restoration")
        self.deleted_at = None
        self.updated_at = utc_now()
    
    def set_session_type(self, session_type: SessionType) -> None:
        if self.deleted_at:
            raise DomainError("Cannot update deleted session")
        self.session_type = session_type
        self.updated_at = utc_now()

    def set_category(
        self,
        category: SessionCategory,
        headcount: int | None = None,
    ) -> None:
        if self.deleted_at:
            raise DomainError("Cannot update deleted session")
        if category == SessionCategory.GROUP:
            if headcount is not None and headcount < 2:
                raise DomainError("Group sessions require at least 2 participants")
        self.category = category
        if headcount is not None:
            self.headcount = headcount
        self.updated_at = utc_now()

    def set_clinical_details(
        self,
        issue_topic: str | None = None,
        diagnosis_type_id: str | None = None,
        diagnosis_id: str | None = None,
        approved_by: str | None = None,
        rate_ugx: int | None = None,
    ) -> None:
        if self.deleted_at:
            raise DomainError("Cannot update deleted session")
        if issue_topic is not None:
            self.issue_topic = issue_topic
        if diagnosis_type_id is not None:
            self.diagnosis_type_id = diagnosis_type_id
        if diagnosis_id is not None:
            self.diagnosis_id = diagnosis_id
        if approved_by is not None:
            self.approved_by = approved_by
        if rate_ugx is not None:
            if rate_ugx < 0:
                raise DomainError("Rate cannot be negative")
            self.rate_ugx = rate_ugx
        self.updated_at = utc_now()

    def set_partner_details(
        self,
        partner_name: str | None,
        partner_relationship: str | None,
    ) -> None:
        if self.deleted_at:
            raise DomainError("Cannot update deleted session")
        if self.category not in {SessionCategory.FAMILY, SessionCategory.COUPLES}:
            raise DomainError("Partner details only apply to family or couples sessions")
        self.partner_name = partner_name
        self.partner_relationship = partner_relationship
        self.updated_at = utc_now()

    def set_clinical_outcome(self, outcome: SessionClinicalStatus) -> None:
        if self.deleted_at:
            raise DomainError("Cannot update deleted session")
        self.clinical_outcome = outcome
        self.updated_at = utc_now()

    def set_client_type(self, client_type: ClientType) -> None:
        if self.deleted_at:
            raise DomainError("Cannot update deleted session")
        self.client_type = client_type
        self.updated_at = utc_now()

    def is_active(self) -> bool:
        """Check if session is active (scheduled or rescheduled)"""
        return self.status in {SessionStatus.SCHEDULED, SessionStatus.RESCHEDULED} and self.deleted_at is None

    # === Public Properties ===

    def clear_events(self) -> None:
        self.events.clear()