"""Utilisation event repository impl (Phase 2 #D-Pricing)."""

from datetime import date

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.entities.utilisation_event import UtilisationEventEntity
from app.domain.repositories.utilisation_event_repository import (
    UtilisationEventRepository,
)
from app.domain.value_objects.core import (
    ContractId,
    TenantId,
    UtilisationEventId,
)
from app.infrastructure.mappers.utilisation_event_mapper import (
    UtilisationEventMapper,
)
from app.infrastructure.models.contract_model import ContractModel
from app.infrastructure.models.utilisation_event_model import (
    UtilisationEventModel,
)


class UtilisationEventRepositoryImpl(UtilisationEventRepository):
    def __init__(self, session: AsyncSession):
        self._session = session

    async def get_by_id(self, entity_id: UtilisationEventId) -> UtilisationEventEntity | None:
        row = await self._session.get(UtilisationEventModel, entity_id.value)
        return UtilisationEventMapper.to_entity(row) if row else None

    async def save(self, entity: UtilisationEventEntity) -> None:
        existing = await self._session.get(UtilisationEventModel, entity.id.value)
        if existing is None:
            self._session.add(UtilisationEventMapper.to_model(entity))
        else:
            existing.event_type = entity.event_type
            existing.occurred_on = entity.occurred_on
            existing.units = entity.units
            existing.service_code = entity.service_code
            existing.source_id = entity.source_id
            existing.notes = entity.notes
            existing.updated_at = entity.updated_at
        await self._session.flush()

    async def delete(self, entity_id: UtilisationEventId) -> None:
        existing = await self._session.get(UtilisationEventModel, entity_id.value)
        if existing is not None:
            await self._session.delete(existing)
            await self._session.flush()

    async def exists(self, entity_id: UtilisationEventId) -> bool:
        existing = await self._session.get(UtilisationEventModel, entity_id.value)
        return existing is not None

    async def list_for_contract(
        self,
        tenant_id: TenantId,
        contract_id: ContractId,
        *,
        from_date: date | None = None,
        to_date: date | None = None,
    ) -> list[UtilisationEventEntity]:
        stmt = (
            select(UtilisationEventModel)
            .where(
                UtilisationEventModel.tenant_id == tenant_id.value,
                UtilisationEventModel.contract_id == contract_id.value,
            )
            .order_by(UtilisationEventModel.occurred_on)
        )
        if from_date is not None:
            stmt = stmt.where(UtilisationEventModel.occurred_on >= from_date)
        if to_date is not None:
            stmt = stmt.where(UtilisationEventModel.occurred_on <= to_date)
        rows = (await self._session.execute(stmt)).scalars().all()
        return [UtilisationEventMapper.to_entity(r) for r in rows]

    async def list_for_client(
        self,
        tenant_id: TenantId,
        client_id: str,
        *,
        limit: int,
        offset: int,
    ) -> list[UtilisationEventEntity]:
        stmt = (
            select(UtilisationEventModel)
            .join(ContractModel, ContractModel.id == UtilisationEventModel.contract_id)
            .where(
                UtilisationEventModel.tenant_id == tenant_id.value,
                ContractModel.client_id == client_id,
            )
            .order_by(UtilisationEventModel.occurred_on.desc())
            .limit(limit)
            .offset(offset)
        )
        rows = (await self._session.execute(stmt)).scalars().all()
        return [UtilisationEventMapper.to_entity(r) for r in rows]

    async def count_for_client(self, tenant_id: TenantId, client_id: str) -> int:
        stmt = (
            select(func.count(UtilisationEventModel.id))
            .join(ContractModel, ContractModel.id == UtilisationEventModel.contract_id)
            .where(
                UtilisationEventModel.tenant_id == tenant_id.value,
                ContractModel.client_id == client_id,
            )
        )
        return int((await self._session.execute(stmt)).scalar() or 0)
