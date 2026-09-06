"""SQLAlchemy implementation of the non-compete clause repository (Phase 2 #D-Provider)."""

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.entities.non_compete_clause import NonCompeteClauseEntity
from app.domain.repositories.non_compete_clause_repository import (
    NonCompeteClauseRepository,
)
from app.domain.value_objects.core import (
    NonCompeteClauseId,
    ProviderId,
    TenantId,
)
from app.infrastructure.mappers.non_compete_clause_mapper import (
    NonCompeteClauseMapper,
)
from app.infrastructure.models.non_compete_clause_model import (
    NonCompeteClauseModel,
)


class NonCompeteClauseRepositoryImpl(NonCompeteClauseRepository):
    def __init__(self, session: AsyncSession):
        self._session = session

    async def get_by_id(self, entity_id: NonCompeteClauseId) -> NonCompeteClauseEntity | None:
        row = await self._session.get(NonCompeteClauseModel, entity_id.value)
        return NonCompeteClauseMapper.to_entity(row) if row else None

    async def save(self, entity: NonCompeteClauseEntity) -> None:
        existing = await self._session.get(NonCompeteClauseModel, entity.id.value)
        if existing is None:
            self._session.add(NonCompeteClauseMapper.to_model(entity))
        else:
            existing.status = entity.status
            existing.terms_summary = entity.terms_summary
            existing.effective_from = entity.effective_from
            existing.effective_until = entity.effective_until
            existing.signed_at = entity.signed_at
            existing.signed_by = entity.signed_by.value if entity.signed_by else None
            existing.revoked_at = entity.revoked_at
            existing.revoked_reason = entity.revoked_reason
            existing.document_id = entity.document_id
            existing.updated_at = entity.updated_at
        await self._session.flush()

    async def delete(self, entity_id: NonCompeteClauseId) -> None:
        existing = await self._session.get(NonCompeteClauseModel, entity_id.value)
        if existing is not None:
            await self._session.delete(existing)
            await self._session.flush()

    async def exists(self, entity_id: NonCompeteClauseId) -> bool:
        existing = await self._session.get(NonCompeteClauseModel, entity_id.value)
        return existing is not None

    async def list_for_provider(
        self, tenant_id: TenantId, provider_id: ProviderId
    ) -> list[NonCompeteClauseEntity]:
        stmt = (
            select(NonCompeteClauseModel)
            .where(
                NonCompeteClauseModel.tenant_id == tenant_id.value,
                NonCompeteClauseModel.provider_id == provider_id.value,
            )
            .order_by(NonCompeteClauseModel.created_at.desc())
        )
        rows = (await self._session.execute(stmt)).scalars().all()
        return [NonCompeteClauseMapper.to_entity(r) for r in rows]
