"""SQLAlchemy implementation of the DSAR repository (Phase 4 #DSAR)."""

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.entities.dsar_request import DSARRequest
from app.domain.repositories.dsar_repository import DSARRequestRepository
from app.domain.value_objects.core import (
    DSARRequestId,
    PersonId,
    TenantId,
)
from app.infrastructure.mappers.dsar_mapper import DSARRequestMapper
from app.infrastructure.models.dsar_model import DSARRequestModel


class DSARRequestRepositoryImpl(DSARRequestRepository):
    def __init__(self, session: AsyncSession):
        self._session = session

    async def get_by_id(self, entity_id: DSARRequestId) -> DSARRequest | None:
        row = await self._session.get(DSARRequestModel, entity_id.value)
        return DSARRequestMapper.to_entity(row) if row else None

    async def save(self, entity: DSARRequest) -> None:
        existing = await self._session.get(DSARRequestModel, entity.id.value)
        new_model = DSARRequestMapper.to_model(entity)
        if existing is None:
            self._session.add(new_model)
        else:
            existing.subject_person_id = new_model.subject_person_id
            existing.request_type = new_model.request_type
            existing.status = new_model.status
            existing.started_at = new_model.started_at
            existing.completed_at = new_model.completed_at
            existing.failed_reason = new_model.failed_reason
            existing.output = new_model.output
            existing.erasure_executes_at = new_model.erasure_executes_at
            existing.updated_at = new_model.updated_at
        await self._session.flush()

    async def delete(self, entity_id: DSARRequestId) -> None:
        existing = await self._session.get(DSARRequestModel, entity_id.value)
        if existing is not None:
            await self._session.delete(existing)
            await self._session.flush()

    async def exists(self, entity_id: DSARRequestId) -> bool:
        existing = await self._session.get(DSARRequestModel, entity_id.value)
        return existing is not None

    async def list_for_tenant(
        self, tenant_id: TenantId, *, limit: int = 100, offset: int = 0
    ) -> list[DSARRequest]:
        stmt = (
            select(DSARRequestModel)
            .where(DSARRequestModel.tenant_id == tenant_id.value)
            .order_by(DSARRequestModel.created_at.desc())
            .limit(limit)
            .offset(offset)
        )
        rows = (await self._session.execute(stmt)).scalars().all()
        return [DSARRequestMapper.to_entity(r) for r in rows]

    async def list_for_subject(
        self, tenant_id: TenantId, subject_person_id: PersonId
    ) -> list[DSARRequest]:
        stmt = (
            select(DSARRequestModel)
            .where(
                DSARRequestModel.tenant_id == tenant_id.value,
                DSARRequestModel.subject_person_id == subject_person_id.value,
            )
            .order_by(DSARRequestModel.created_at.desc())
        )
        rows = (await self._session.execute(stmt)).scalars().all()
        return [DSARRequestMapper.to_entity(r) for r in rows]
