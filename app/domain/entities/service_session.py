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
    _id: SessionId
    _tenant_id: TenantId
    _service_id: ServiceId
    _provider_id: PersonId
    _person_id: PersonId
    _scheduled_at: datetime
    _status: SessionStatus
    _created_at: datetime
    _updated_at: datetime
    _reschedule_count: int
    
    # Optional fields (with defaults)
    _completed_at: datetime | None = None
    _duration: int | None = None
    _location: str | None = None
    _notes: str | None = None
    _feedback: str | None = None
    _cancellation_reason: str | None = None
    _deleted_at: datetime | None = None
    _events: list[DomainEvent] = field(default_factory=list)
    
    def complete(self, duration: int, notes: str | None = None) -> None:
        if self._status not in {SessionStatus.SCHEDULED, SessionStatus.RESCHEDULED}:
            raise DomainError("Only scheduled sessions can be completed")
        if duration <= 0:
            raise DomainError("Duration must be positive")
        if not notes:
            raise DomainError("Notes are required for completed session")
        self._status = SessionStatus.COMPLETED
        self._completed_at = utc_now()
        self._duration = duration
        self._notes = notes
        self._events.append(SessionCompleted(occurred_at=utc_now(), session_id=self._id, person_id=self._person_id))
    
    def cancel(self, reason: str) -> None:
        """Cancel a session"""
        if self._deleted_at:
            raise DomainError("Cannot cancel deleted session")
        if self._status in {SessionStatus.COMPLETED, SessionStatus.CANCELLED, SessionStatus.NO_SHOW}:
            raise DomainError("Cannot cancel completed or finalized session")
        if not reason:
            raise DomainError("Cancellation requires reason")
        self._status = SessionStatus.CANCELLED
        self._cancellation_reason = reason
        self._updated_at = utc_now()
        self._events.append(SessionCancelled(occurred_at=utc_now(), session_id=self._id, reason=reason))
    
    def reschedule(self, new_scheduled_at: datetime) -> None:
        """Reschedule a session"""
        if self._deleted_at:
            raise DomainError("Cannot reschedule deleted session")
        if self._status in {SessionStatus.COMPLETED, SessionStatus.CANCELLED, SessionStatus.NO_SHOW}:
            raise DomainError("Cannot reschedule completed or finalized session")
        if new_scheduled_at <= utc_now():
            raise DomainError("New scheduled time must be in the future")
        self._status = SessionStatus.RESCHEDULED
        self._scheduled_at = new_scheduled_at
        self._reschedule_count += 1
        self._updated_at = utc_now()
        self._events.append(SessionRescheduled(occurred_at=utc_now(), session_id=self._id, new_scheduled_at=new_scheduled_at))
    
    def mark_no_show(self) -> None:
        """Mark a session as no-show"""
        if self._deleted_at:
            raise DomainError("Cannot mark deleted session as no-show")
        if self._status in {SessionStatus.COMPLETED, SessionStatus.CANCELLED, SessionStatus.NO_SHOW}:
            raise DomainError("Cannot mark completed or finalized session as no-show")
        self._status = SessionStatus.NO_SHOW
        self._updated_at = utc_now()
    
    def update_location(self, location: str | None) -> None:
        """Update session location"""
        if self._deleted_at:
            raise DomainError("Cannot update location for deleted session")
        if self._status in {SessionStatus.COMPLETED, SessionStatus.CANCELLED}:
            raise DomainError("Cannot update location for completed or cancelled session")
        self._location = location
        self._updated_at = utc_now()
    
    def update_notes(self, notes: str | None) -> None:
        """Update session notes"""
        if self._deleted_at:
            raise DomainError("Cannot update notes for deleted session")
        self._notes = notes
        self._updated_at = utc_now()
    
    def update_feedback(self, feedback: str | None) -> None:
        """Update session feedback"""
        if self._deleted_at:
            raise DomainError("Cannot update feedback for deleted session")
        if self._status != SessionStatus.COMPLETED:
            raise DomainError("Feedback can only be added to completed sessions")
        self._feedback = feedback
        self._updated_at = utc_now()
    
    def archive(self) -> None:
        """Archive a session"""
        if self._deleted_at:
            raise DomainError("Cannot archive deleted session")
        # Archive is a soft delete operation
        self._deleted_at = utc_now()
        self._updated_at = utc_now()
    
    def restore(self) -> None:
        """Restore an archived session"""
        if not self._deleted_at:
            raise DomainError("Session is not archived and does not need restoration")
        self._deleted_at = None
        self._updated_at = utc_now()
    
    def is_active(self) -> bool:
        """Check if session is active (scheduled or rescheduled)"""
        return self._status in {SessionStatus.SCHEDULED, SessionStatus.RESCHEDULED} and self._deleted_at is None

    # === Public Properties ===

    @property
    def id(self) -> SessionId:
        return self._id

    @property
    def tenant_id(self) -> TenantId:
        return self._tenant_id

    @property
    def service_id(self) -> ServiceId:
        return self._service_id

    @property
    def provider_id(self) -> PersonId:
        return self._provider_id

    @property
    def person_id(self) -> PersonId:
        return self._person_id

    @property
    def scheduled_at(self) -> datetime:
        return self._scheduled_at

    @property
    def status(self) -> SessionStatus:
        return self._status

    @property
    def reschedule_count(self) -> int:
        return self._reschedule_count

    @property
    def completed_at(self) -> datetime | None:
        return self._completed_at

    @property
    def duration(self) -> int | None:
        return self._duration

    @property
    def location(self) -> str | None:
        return self._location

    @property
    def notes(self) -> str | None:
        return self._notes

    @property
    def feedback(self) -> str | None:
        return self._feedback

    @property
    def cancellation_reason(self) -> str | None:
        return self._cancellation_reason

    @property
    def created_at(self) -> datetime:
        return self._created_at

    @property
    def updated_at(self) -> datetime:
        return self._updated_at

    @property
    def deleted_at(self) -> datetime | None:
        return self._deleted_at

    @property
    def events(self) -> list[DomainEvent]:
        return list(self._events)

    def clear_events(self) -> None:
        self._events.clear()