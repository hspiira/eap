"""SQLAlchemy implementation of the Critical Incident repository (Phase 2 #D-CISM)."""

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.entities.critical_incident import CriticalIncidentEntity
from app.domain.repositories.critical_incident_repository import (
    CriticalIncidentRepository,
)
from app.domain.value_objects.core import CriticalIncidentId, TenantId
from app.infrastructure.mappers.critical_incident_mapper import (
    CriticalIncidentMapper,
)
from app.infrastructure.models.critical_incident_model import CriticalIncidentModel


class CriticalIncidentRepositoryImpl(CriticalIncidentRepository):
    def __init__(self, session: AsyncSession):
        self._session = session

    async def get_by_id(self, entity_id: CriticalIncidentId) -> CriticalIncidentEntity | None:
        stmt = select(CriticalIncidentModel).where(CriticalIncidentModel.id == entity_id.value)
        row = (await self._session.execute(stmt)).scalar_one_or_none()
        return CriticalIncidentMapper.to_entity(row) if row else None

    async def save(self, entity: CriticalIncidentEntity) -> None:
        existing = await self._session.get(CriticalIncidentModel, entity.id.value)
        if existing is None:
            self._session.add(CriticalIncidentMapper.to_model(entity))
        else:
            existing.event_description = entity.event_description
            existing.severity = entity.severity
            existing.affected_population_size = entity.affected_population_size
            existing.status = entity.status
            existing.phases = [
                {
                    "phase": p.phase.value,
                    "occurred_at": p.occurred_at.isoformat(),
                    "notes": p.notes,
                }
                for p in entity.phases
            ]
            existing.after_action_summary = entity.after_action_summary
            existing.closed_at = entity.closed_at
            existing.updated_at = entity.updated_at
        await self._session.flush()

    async def delete(self, entity_id: CriticalIncidentId) -> None:
        existing = await self._session.get(CriticalIncidentModel, entity_id.value)
        if existing is not None:
            await self._session.delete(existing)
            await self._session.flush()

    async def exists(self, entity_id: CriticalIncidentId) -> bool:
        existing = await self._session.get(CriticalIncidentModel, entity_id.value)
        return existing is not None

    async def list_for_tenant(
        self,
        tenant_id: TenantId,
        *,
        limit: int = 100,
        offset: int = 0,
    ) -> list[CriticalIncidentEntity]:
        stmt = (
            select(CriticalIncidentModel)
            .where(CriticalIncidentModel.tenant_id == tenant_id.value)
            .order_by(CriticalIncidentModel.occurred_at.desc())
            .limit(limit)
            .offset(offset)
        )
        rows = (await self._session.execute(stmt)).scalars().all()
        return [CriticalIncidentMapper.to_entity(r) for r in rows]
