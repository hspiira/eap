"""Critical Incident repository port (Phase 2 #D-CISM)."""

from app.domain.entities.critical_incident import CriticalIncidentEntity
from app.domain.repositories.base_repository import BaseRepository
from app.domain.value_objects.core import CriticalIncidentId, TenantId


class CriticalIncidentRepository(
    BaseRepository[CriticalIncidentEntity, CriticalIncidentId]
):
    async def list_for_tenant(
        self,
        tenant_id: TenantId,
        *,
        limit: int = 100,
        offset: int = 0,
    ) -> list[CriticalIncidentEntity]:
        ...
