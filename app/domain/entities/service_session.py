"""
Service Session Entity (Aggregate Root)

Represents an individual service delivery session.
"""

from dataclasses import dataclass, field
from datetime import datetime
from app.domain.value_objects.core import SessionId, TenantId, ServiceId, PersonId
from app.domain.enums import SessionStatus
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
    
    def is_active(self) -> bool:
        """Check if session is active (scheduled or rescheduled)"""
        return self.status in {SessionStatus.SCHEDULED, SessionStatus.RESCHEDULED} and self.deleted_at is None

    # === Public Properties ===

    def clear_events(self) -> None:
        self.events.clear()