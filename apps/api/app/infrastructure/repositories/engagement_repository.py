"""SQLAlchemy implementation of the Engagement repository (Phase 4 #D-Engagement)."""

from sqlalchemy import Select, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.entities.engagement import Engagement
from app.domain.enums import EngagementStatus
from app.domain.repositories.engagement_repository import EngagementRepository
from app.domain.value_objects.core import ClientId, EngagementId, TenantId
from app.infrastructure.mappers.engagement_mapper import EngagementMapper
from app.infrastructure.models.engagement_model import EngagementModel

_SORTABLE = {
    "created_at": EngagementModel.created_at,
    "updated_at": EngagementModel.updated_at,
    "name": EngagementModel.name,
    "status": EngagementModel.status,
    "period_start": EngagementModel.period_start,
    "period_end": EngagementModel.period_end,
}


def _filtered(
    stmt: Select,
    tenant_id: TenantId,
    *,
    status: EngagementStatus | None,
    client_id: ClientId | None,
    search: str | None,
) -> Select:
    """Apply the tenant scope and the list filters shared by list and count."""
    stmt = stmt.where(EngagementModel.tenant_id == tenant_id.value)
    if status is not None:
        stmt = stmt.where(EngagementModel.status == status)
    if client_id is not None:
        stmt = stmt.where(EngagementModel.client_id == client_id.value)
    if search:
        stmt = stmt.where(EngagementModel.name.ilike(f"%{search}%"))
    return stmt


class EngagementRepositoryImpl(EngagementRepository):
    def __init__(self, session: AsyncSession):
        self._session = session

    async def get_by_id(self, entity_id: EngagementId) -> Engagement | None:
        row = await self._session.get(EngagementModel, entity_id.value)
        return EngagementMapper.to_entity(row) if row else None

    async def save(self, entity: Engagement) -> None:
        existing = await self._session.get(EngagementModel, entity.id.value)
        new_model = EngagementMapper.to_model(entity)
        if existing is None:
            self._session.add(new_model)
        else:
            existing.client_id = new_model.client_id
            existing.name = new_model.name
            existing.description = new_model.description
            existing.status = new_model.status
            existing.period_start = new_model.period_start
            existing.period_end = new_model.period_end
            existing.deliverables = new_model.deliverables
            existing.hours_log = new_model.hours_log
            existing.activated_at = new_model.activated_at
            existing.delivered_at = new_model.delivered_at
            existing.invoiced_at = new_model.invoiced_at
            existing.closed_at = new_model.closed_at
            existing.updated_at = new_model.updated_at
        await self._session.flush()

    async def delete(self, entity_id: EngagementId) -> None:
        existing = await self._session.get(EngagementModel, entity_id.value)
        if existing is not None:
            await self._session.delete(existing)
            await self._session.flush()

    async def exists(self, entity_id: EngagementId) -> bool:
        existing = await self._session.get(EngagementModel, entity_id.value)
        return existing is not None

    async def list_for_tenant(
        self,
        tenant_id: TenantId,
        *,
        status: EngagementStatus | None = None,
        client_id: ClientId | None = None,
        search: str | None = None,
        limit: int = 50,
        offset: int = 0,
        sort_by: str = "created_at",
        sort_desc: bool = True,
    ) -> list[Engagement]:
        column = _SORTABLE.get(sort_by, EngagementModel.created_at)
        stmt = _filtered(
            select(EngagementModel), tenant_id, status=status, client_id=client_id, search=search
        )
        stmt = (
            stmt.order_by(column.desc() if sort_desc else column.asc()).limit(limit).offset(offset)
        )
        rows = (await self._session.execute(stmt)).scalars().all()
        return [EngagementMapper.to_entity(r) for r in rows]

    async def count_for_tenant(
        self,
        tenant_id: TenantId,
        *,
        status: EngagementStatus | None = None,
        client_id: ClientId | None = None,
        search: str | None = None,
    ) -> int:
        stmt = _filtered(
            select(func.count()).select_from(EngagementModel),
            tenant_id,
            status=status,
            client_id=client_id,
            search=search,
        )
        return int((await self._session.execute(stmt)).scalar_one())

    async def list_for_client(
        self,
        tenant_id: TenantId,
        client_id: ClientId,
        *,
        limit: int = 100,
    ) -> list[Engagement]:
        stmt = (
            select(EngagementModel)
            .where(
                EngagementModel.tenant_id == tenant_id.value,
                EngagementModel.client_id == client_id.value,
            )
            .order_by(EngagementModel.created_at.desc())
            .limit(limit)
        )
        rows = (await self._session.execute(stmt)).scalars().all()
        return [EngagementMapper.to_entity(r) for r in rows]
