"""Critical Incident use cases (Phase 2 #D-CISM).

Lifecycle / phase recording flows through TransitionUseCase + CriticalIncidentTransition.
Only the create path needs bespoke construction.
"""

from datetime import datetime

from app.application.use_cases.base import BaseUseCase
from app.domain.entities.critical_incident import CriticalIncidentEntity
from app.domain.enums import CriticalIncidentSeverity, CriticalIncidentStatus
from app.domain.repositories.critical_incident_repository import (
    CriticalIncidentRepository,
)
from app.domain.value_objects.core import (
    ClientId,
    CriticalIncidentId,
    TenantId,
    UserId,
)
from app.shared.utils.datetime import utc_now


class CreateCriticalIncidentUseCase(
    BaseUseCase[CriticalIncidentEntity, CriticalIncidentId]
):
    """Log a new critical incident and emit ``CriticalIncidentLogged``."""

    def __init__(self, repository: CriticalIncidentRepository):
        super().__init__(repository)

    async def execute(
        self,
        *,
        incident_id: CriticalIncidentId,
        tenant_id: TenantId,
        client_id: ClientId,
        event_description: str,
        severity: CriticalIncidentSeverity,
        affected_population_size: int,
        occurred_at: datetime,
        logged_by: UserId,
    ) -> CriticalIncidentEntity:
        now = utc_now()
        incident = CriticalIncidentEntity(
            id=incident_id,
            tenant_id=tenant_id,
            client_id=client_id,
            event_description=event_description,
            severity=severity,
            affected_population_size=affected_population_size,
            occurred_at=occurred_at,
            logged_by=logged_by,
            status=CriticalIncidentStatus.OPEN,
            created_at=now,
            updated_at=now,
        )
        return await self._save_and_publish_events(incident)


class GetCriticalIncidentUseCase(
    BaseUseCase[CriticalIncidentEntity, CriticalIncidentId]
):
    def __init__(self, repository: CriticalIncidentRepository):
        super().__init__(repository)
        self._repo = repository

    async def execute(
        self, incident_id: CriticalIncidentId
    ) -> CriticalIncidentEntity | None:
        return await self._repo.get_by_id(incident_id)

    async def list_for_tenant(
        self, tenant_id: TenantId, *, limit: int = 100, offset: int = 0
    ) -> list[CriticalIncidentEntity]:
        return await self._repo.list_for_tenant(
            tenant_id, limit=limit, offset=offset
        )
