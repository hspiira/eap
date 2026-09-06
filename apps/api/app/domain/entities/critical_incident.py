"""Critical Incident entity (Phase 2 #D-CISM / SAD §5.2.9, §2.6).

Represents a workplace event (fatality, fraud, robbery, mass redundancy, etc.)
that triggers acute psychological need. Tracks severity, affected population,
and the multi-phase Mitchell-Everly response timeline. Linked sessions live
on ``service_sessions.incident_id`` (nullable FK); that backreference is the
audit trail of what counselling work was delivered as part of the response.
"""

from dataclasses import dataclass, field
from datetime import datetime

from app.domain.enums import (
    CriticalIncidentPhase,
    CriticalIncidentSeverity,
    CriticalIncidentStatus,
)
from app.domain.events import (
    CriticalIncidentClosed,
    CriticalIncidentLogged,
    CriticalIncidentPhaseRecorded,
    DomainEvent,
)
from app.domain.exceptions import ConflictError, DomainError
from app.domain.value_objects.core import (
    ClientId,
    CriticalIncidentId,
    TenantId,
    UserId,
)
from app.shared.utils.datetime import utc_now


@dataclass(frozen=True)
class IncidentPhaseEntry:
    """One entry on the response timeline."""

    phase: CriticalIncidentPhase
    occurred_at: datetime
    notes: str | None = None


@dataclass
class CriticalIncidentEntity:
    """Aggregate root for an in-progress or closed CISM response."""

    id: CriticalIncidentId
    tenant_id: TenantId
    client_id: ClientId
    event_description: str
    severity: CriticalIncidentSeverity
    affected_population_size: int
    occurred_at: datetime
    logged_by: UserId
    status: CriticalIncidentStatus
    created_at: datetime
    updated_at: datetime
    after_action_summary: str | None = None
    closed_at: datetime | None = None
    phases: list[IncidentPhaseEntry] = field(default_factory=list[IncidentPhaseEntry])
    events: list[DomainEvent] = field(default_factory=list[DomainEvent])

    def __post_init__(self) -> None:
        if not self.event_description:
            raise DomainError("Critical incident requires an event description")
        if self.affected_population_size < 0:
            raise DomainError("Affected population size cannot be negative")
        if self.created_at == self.updated_at and not self.events:
            self.events.append(
                CriticalIncidentLogged(
                    occurred_at=self.created_at,
                    incident_id=self.id,
                    severity=self.severity,
                    affected_population_size=self.affected_population_size,
                )
            )

    def record_phase(
        self,
        phase: CriticalIncidentPhase,
        notes: str | None = None,
        now: datetime | None = None,
    ) -> None:
        """Append a phase entry; auto-advances status from OPEN to IN_RESPONSE."""
        if self.status == CriticalIncidentStatus.CLOSED:
            raise DomainError("Cannot add phases to a closed incident")
        now = now or utc_now()
        self.phases.append(IncidentPhaseEntry(phase=phase, occurred_at=now, notes=notes))
        if self.status == CriticalIncidentStatus.OPEN:
            self.status = CriticalIncidentStatus.IN_RESPONSE
        self.updated_at = now
        self.events.append(
            CriticalIncidentPhaseRecorded(occurred_at=now, incident_id=self.id, phase=phase)
        )

    def close(self, after_action_summary: str, now: datetime | None = None) -> None:
        """Close the response and capture the after-action summary."""
        if self.status == CriticalIncidentStatus.CLOSED:
            raise ConflictError("Incident is already closed")
        if not after_action_summary:
            raise DomainError("Closing an incident requires an after-action summary")
        now = now or utc_now()
        self.status = CriticalIncidentStatus.CLOSED
        self.after_action_summary = after_action_summary
        self.closed_at = now
        self.updated_at = now
        self.events.append(CriticalIncidentClosed(occurred_at=now, incident_id=self.id))

    def after_action_report(self) -> dict[str, object]:
        """Return a JSON-serialisable after-action summary."""
        return {
            "incident_id": self.id.value,
            "client_id": self.client_id.value,
            "event_description": self.event_description,
            "severity": self.severity.value,
            "affected_population_size": self.affected_population_size,
            "occurred_at": self.occurred_at.isoformat(),
            "status": self.status.value,
            "phase_count": len(self.phases),
            "phases": [
                {
                    "phase": p.phase.value,
                    "occurred_at": p.occurred_at.isoformat(),
                    "notes": p.notes,
                }
                for p in self.phases
            ],
            "after_action_summary": self.after_action_summary,
            "closed_at": self.closed_at.isoformat() if self.closed_at else None,
        }
