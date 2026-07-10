"""Critical Incident mapper (Phase 2 #D-CISM)."""

from app.domain.entities.critical_incident import (
    CriticalIncidentEntity,
    IncidentPhaseEntry,
)
from app.domain.enums import (
    CriticalIncidentPhase,
    CriticalIncidentSeverity,
    CriticalIncidentStatus,
)
from app.domain.value_objects.core import (
    ClientId,
    CriticalIncidentId,
    TenantId,
    UserId,
)
from app.infrastructure.models.critical_incident_model import CriticalIncidentModel
from app.shared.utils.datetime import ensure_utc


class CriticalIncidentMapper:
    @staticmethod
    def to_entity(model: CriticalIncidentModel) -> CriticalIncidentEntity:
        phases = [
            IncidentPhaseEntry(
                phase=CriticalIncidentPhase(p["phase"]),
                occurred_at=ensure_utc(_parse_iso(p["occurred_at"])),
                notes=p.get("notes"),
            )
            for p in (model.phases or [])
        ]
        entity = CriticalIncidentEntity(
            id=CriticalIncidentId(model.id),
            tenant_id=TenantId(model.tenant_id),
            client_id=ClientId(model.client_id),
            event_description=model.event_description,
            severity=CriticalIncidentSeverity(model.severity),
            affected_population_size=model.affected_population_size,
            occurred_at=ensure_utc(model.occurred_at),
            logged_by=UserId(model.logged_by),
            status=CriticalIncidentStatus(model.status),
            after_action_summary=model.after_action_summary,
            closed_at=ensure_utc(model.closed_at) if model.closed_at else None,
            phases=phases,
            created_at=ensure_utc(model.created_at),
            updated_at=ensure_utc(model.updated_at),
        )
        entity.events.clear()  # already-persisted entity has no pending events
        return entity

    @staticmethod
    def to_model(entity: CriticalIncidentEntity) -> CriticalIncidentModel:
        return CriticalIncidentModel(
            id=entity.id.value,
            tenant_id=entity.tenant_id.value,
            client_id=entity.client_id.value,
            event_description=entity.event_description,
            severity=entity.severity,
            affected_population_size=entity.affected_population_size,
            occurred_at=ensure_utc(entity.occurred_at),
            logged_by=entity.logged_by.value,
            status=entity.status,
            phases=[
                {
                    "phase": p.phase.value,
                    "occurred_at": p.occurred_at.isoformat(),
                    "notes": p.notes,
                }
                for p in entity.phases
            ],
            after_action_summary=entity.after_action_summary,
            closed_at=ensure_utc(entity.closed_at) if entity.closed_at else None,
            created_at=ensure_utc(entity.created_at),
            updated_at=ensure_utc(entity.updated_at),
        )


def _parse_iso(value: str):
    from datetime import datetime

    return datetime.fromisoformat(value)
