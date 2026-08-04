"""SQLAlchemy implementation of the benchmark-consent repository (Phase 4 #D-Benchmark)."""

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.entities.benchmark_consent import BenchmarkConsent
from app.domain.enums import BenchmarkScope, TenantConsentStatus
from app.domain.repositories.benchmark_consent_repository import (
    BenchmarkConsentRepository,
)
from app.domain.value_objects.core import (
    BenchmarkConsentId,
    TenantId,
)
from app.infrastructure.mappers.benchmark_consent_mapper import (
    BenchmarkConsentMapper,
)
from app.infrastructure.models.benchmark_consent_model import (
    BenchmarkConsentModel,
)


class BenchmarkConsentRepositoryImpl(BenchmarkConsentRepository):
    def __init__(self, session: AsyncSession):
        self._session = session

    async def get_by_id(self, entity_id: BenchmarkConsentId) -> BenchmarkConsent | None:
        row = await self._session.get(BenchmarkConsentModel, entity_id.value)
        return BenchmarkConsentMapper.to_entity(row) if row else None

    async def save(self, entity: BenchmarkConsent) -> None:
        existing = await self._session.get(BenchmarkConsentModel, entity.id.value)
        new_model = BenchmarkConsentMapper.to_model(entity)
        if existing is None:
            self._session.add(new_model)
        else:
            existing.scope = new_model.scope
            existing.status = new_model.status
            existing.version = new_model.version
            existing.granted_by = new_model.granted_by
            existing.granted_at = new_model.granted_at
            existing.withdrawn_at = new_model.withdrawn_at
            existing.withdrawn_by = new_model.withdrawn_by
            existing.withdrawn_reason = new_model.withdrawn_reason
            existing.updated_at = new_model.updated_at
        await self._session.flush()

    async def delete(self, entity_id: BenchmarkConsentId) -> None:
        existing = await self._session.get(BenchmarkConsentModel, entity_id.value)
        if existing is not None:
            await self._session.delete(existing)
            await self._session.flush()

    async def exists(self, entity_id: BenchmarkConsentId) -> bool:
        existing = await self._session.get(BenchmarkConsentModel, entity_id.value)
        return existing is not None

    async def list_for_tenant(self, tenant_id: TenantId) -> list[BenchmarkConsent]:
        stmt = (
            select(BenchmarkConsentModel)
            .where(BenchmarkConsentModel.tenant_id == tenant_id.value)
            .order_by(BenchmarkConsentModel.created_at.desc())
        )
        rows = (await self._session.execute(stmt)).scalars().all()
        return [BenchmarkConsentMapper.to_entity(r) for r in rows]

    async def list_active_for_scope(self, scope: BenchmarkScope) -> list[BenchmarkConsent]:
        stmt = select(BenchmarkConsentModel).where(
            BenchmarkConsentModel.scope == scope.value,
            BenchmarkConsentModel.status == TenantConsentStatus.ACTIVE.value,
        )
        rows = (await self._session.execute(stmt)).scalars().all()
        return [BenchmarkConsentMapper.to_entity(r) for r in rows]

    async def find_active_for_tenant_scope(
        self, tenant_id: TenantId, scope: BenchmarkScope
    ) -> BenchmarkConsent | None:
        stmt = select(BenchmarkConsentModel).where(
            BenchmarkConsentModel.tenant_id == tenant_id.value,
            BenchmarkConsentModel.scope == scope.value,
            BenchmarkConsentModel.status == TenantConsentStatus.ACTIVE.value,
        )
        row = (await self._session.execute(stmt)).scalar_one_or_none()
        return BenchmarkConsentMapper.to_entity(row) if row else None
