"""Critical Incident entity tests (Phase 2 #D-CISM)."""

from datetime import UTC, datetime

import pytest

from app.domain.entities.critical_incident import CriticalIncidentEntity
from app.domain.enums import (
    CriticalIncidentPhase,
    CriticalIncidentSeverity,
    CriticalIncidentStatus,
)
from app.domain.events import (
    CriticalIncidentClosed,
    CriticalIncidentLogged,
    CriticalIncidentPhaseRecorded,
)
from app.domain.exceptions import DomainError
from app.domain.value_objects.core import (
    ClientId,
    CriticalIncidentId,
    TenantId,
    UserId,
)


def _incident(
    *,
    severity: CriticalIncidentSeverity = CriticalIncidentSeverity.HIGH,
    affected: int = 12,
    status: CriticalIncidentStatus = CriticalIncidentStatus.OPEN,
) -> CriticalIncidentEntity:
    now = datetime.now(UTC)
    return CriticalIncidentEntity(
        id=CriticalIncidentId("ci-1"),
        tenant_id=TenantId("t-1"),
        client_id=ClientId("c-1"),
        event_description="Robbery at branch X",
        severity=severity,
        affected_population_size=affected,
        occurred_at=now,
        logged_by=UserId("usr-1"),
        status=status,
        created_at=now,
        updated_at=now,
    )


class TestCreation:
    def test_logged_event_attached_on_creation(self):
        incident = _incident()
        logged = [e for e in incident.events if isinstance(e, CriticalIncidentLogged)]
        assert len(logged) == 1
        assert logged[0].severity == CriticalIncidentSeverity.HIGH
        assert logged[0].affected_population_size == 12

    def test_event_description_required(self):
        with pytest.raises(DomainError):
            CriticalIncidentEntity(
                id=CriticalIncidentId("ci-1"),
                tenant_id=TenantId("t-1"),
                client_id=ClientId("c-1"),
                event_description="",
                severity=CriticalIncidentSeverity.LOW,
                affected_population_size=1,
                occurred_at=datetime.now(UTC),
                logged_by=UserId("u-1"),
                status=CriticalIncidentStatus.OPEN,
                created_at=datetime.now(UTC),
                updated_at=datetime.now(UTC),
            )

    def test_negative_population_rejected(self):
        with pytest.raises(DomainError):
            _incident(affected=-1)


class TestPhaseRecording:
    def test_first_phase_advances_status_to_in_response(self):
        incident = _incident()
        incident.record_phase(CriticalIncidentPhase.DEFUSING, notes="On-site brief")
        assert incident.status == CriticalIncidentStatus.IN_RESPONSE
        assert len(incident.phases) == 1
        assert incident.phases[0].phase == CriticalIncidentPhase.DEFUSING
        recorded = [
            e for e in incident.events if isinstance(e, CriticalIncidentPhaseRecorded)
        ]
        assert len(recorded) == 1

    def test_subsequent_phases_keep_status(self):
        incident = _incident()
        incident.record_phase(CriticalIncidentPhase.DEFUSING)
        incident.record_phase(CriticalIncidentPhase.DEBRIEFING)
        incident.record_phase(CriticalIncidentPhase.FOLLOW_UP)
        assert incident.status == CriticalIncidentStatus.IN_RESPONSE
        assert len(incident.phases) == 3

    def test_cannot_record_phase_when_closed(self):
        incident = _incident()
        incident.record_phase(CriticalIncidentPhase.DEFUSING)
        incident.close("All staff supported")
        with pytest.raises(DomainError):
            incident.record_phase(CriticalIncidentPhase.DEBRIEFING)


class TestClose:
    def test_close_marks_status_and_records_summary(self):
        incident = _incident()
        incident.record_phase(CriticalIncidentPhase.DEFUSING)
        incident.close("Comprehensive after-action notes")
        assert incident.status == CriticalIncidentStatus.CLOSED
        assert incident.after_action_summary == "Comprehensive after-action notes"
        assert incident.closed_at is not None
        closed = [e for e in incident.events if isinstance(e, CriticalIncidentClosed)]
        assert len(closed) == 1

    def test_cannot_close_twice(self):
        incident = _incident()
        incident.close("Summary one")
        with pytest.raises(DomainError):
            incident.close("Summary two")

    def test_close_requires_summary(self):
        incident = _incident()
        with pytest.raises(DomainError):
            incident.close("")


class TestAfterActionReport:
    def test_report_includes_phases_and_status(self):
        incident = _incident()
        incident.record_phase(CriticalIncidentPhase.DEFUSING, notes="initial")
        incident.record_phase(CriticalIncidentPhase.DEBRIEFING)
        incident.close("done")

        report = incident.after_action_report()
        assert report["incident_id"] == "ci-1"
        assert report["status"] == "Closed"
        assert report["phase_count"] == 2
        assert report["phases"][0]["phase"] == "Defusing"
        assert report["phases"][0]["notes"] == "initial"
        assert report["after_action_summary"] == "done"
