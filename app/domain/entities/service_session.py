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
    _id: SessionId
    _tenant_id: TenantId
    
    _service_id: ServiceId
    _provider_id: PersonId
    _person_id: PersonId
    
    _scheduled_at: datetime
    _completed_at: datetime | None = None
    _duration: int | None = None
    _location: str | None = None
    
    _status: SessionStatus
    _notes: str | None = None
    _feedback: str | None = None
    _cancellation_reason: str | None = None
    _reschedule_count: int
    
    _created_at: datetime
    _updated_at: datetime
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
        if self._status in {SessionStatus.COMPLETED, SessionStatus.CANCELLED, SessionStatus.NO_SHOW}:
            raise DomainError("Cannot cancel completed or finalized session")
        if not reason:
            raise DomainError("Cancellation requires reason")
        self._status = SessionStatus.CANCELLED
        self._cancellation_reason = reason
        self._events.append(SessionCancelled(occurred_at=utc_now(), session_id=self._id, reason=reason))
    
    def reschedule(self, new_scheduled_at: datetime) -> None:
        if self._status in {SessionStatus.COMPLETED, SessionStatus.CANCELLED, SessionStatus.NO_SHOW}:
            raise DomainError("Cannot reschedule completed or finalized session")
        if new_scheduled_at <= utc_now():
            raise DomainError("New scheduled time must be in the future")
        self._status = SessionStatus.RESCHEDULED
        self._scheduled_at = new_scheduled_at
        self._reschedule_count += 1
        self._events.append(SessionRescheduled(occurred_at=utc_now(), session_id=self._id, new_scheduled_at=new_scheduled_at))