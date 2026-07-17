"""SQLAlchemy implementations of the report repositories (Phase 2 #D-Reports)."""

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.entities.report import ReportRun, ReportTemplate
from app.domain.repositories.report_repository import (
    ReportRunRepository,
    ReportTemplateRepository,
)
from app.domain.value_objects.core import (
    ReportRunId,
    ReportTemplateId,
    TenantId,
)
from app.infrastructure.mappers.report_mapper import (
    ReportRunMapper,
    ReportTemplateMapper,
)
from app.infrastructure.models.report_model import (
    ReportRunModel,
    ReportTemplateModel,
)


class ReportTemplateRepositoryImpl(ReportTemplateRepository):
    def __init__(self, session: AsyncSession):
        self._session = session

    async def get_by_id(self, entity_id: ReportTemplateId) -> ReportTemplate | None:
        row = await self._session.get(ReportTemplateModel, entity_id.value)
        return ReportTemplateMapper.to_entity(row) if row else None

    async def save(self, entity: ReportTemplate) -> None:
        existing = await self._session.get(ReportTemplateModel, entity.id.value)
        if existing is None:
            self._session.add(ReportTemplateMapper.to_model(entity))
        else:
            existing.code = entity.code
            existing.name = entity.name
            existing.description = entity.description
            existing.sections = [
                {
                    "title": s.title,
                    "query_type": s.query_type.value,
                    "parameters": s.parameters,
                    "narrative": s.narrative,
                }
                for s in entity.sections
            ]
            existing.is_active = entity.is_active
            existing.updated_at = entity.updated_at
        await self._session.flush()

    async def delete(self, entity_id: ReportTemplateId) -> None:
        existing = await self._session.get(ReportTemplateModel, entity_id.value)
        if existing is not None:
            await self._session.delete(existing)
            await self._session.flush()

    async def exists(self, entity_id: ReportTemplateId) -> bool:
        existing = await self._session.get(ReportTemplateModel, entity_id.value)
        return existing is not None

    async def list_for_tenant(
        self, tenant_id: TenantId, *, active_only: bool = True
    ) -> list[ReportTemplate]:
        stmt = select(ReportTemplateModel).where(ReportTemplateModel.tenant_id == tenant_id.value)
        if active_only:
            stmt = stmt.where(ReportTemplateModel.is_active.is_(True))
        rows = (await self._session.execute(stmt)).scalars().all()
        return [ReportTemplateMapper.to_entity(r) for r in rows]

    async def get_by_code(self, tenant_id: TenantId, code: str) -> ReportTemplate | None:
        stmt = select(ReportTemplateModel).where(
            ReportTemplateModel.tenant_id == tenant_id.value,
            ReportTemplateModel.code == code,
        )
        row = (await self._session.execute(stmt)).scalar_one_or_none()
        return ReportTemplateMapper.to_entity(row) if row else None


class ReportRunRepositoryImpl(ReportRunRepository):
    def __init__(self, session: AsyncSession):
        self._session = session

    async def get_by_id(self, entity_id: ReportRunId) -> ReportRun | None:
        row = await self._session.get(ReportRunModel, entity_id.value)
        return ReportRunMapper.to_entity(row) if row else None

    async def save(self, entity: ReportRun) -> None:
        existing = await self._session.get(ReportRunModel, entity.id.value)
        if existing is None:
            self._session.add(ReportRunMapper.to_model(entity))
        else:
            existing.parameters = entity.parameters
            existing.status = entity.status
            existing.started_at = entity.started_at
            existing.completed_at = entity.completed_at
            existing.output = entity.output
            existing.error = entity.error
            existing.updated_at = entity.updated_at
        await self._session.flush()

    async def delete(self, entity_id: ReportRunId) -> None:
        existing = await self._session.get(ReportRunModel, entity_id.value)
        if existing is not None:
            await self._session.delete(existing)
            await self._session.flush()

    async def exists(self, entity_id: ReportRunId) -> bool:
        existing = await self._session.get(ReportRunModel, entity_id.value)
        return existing is not None

    async def list_for_template(
        self,
        tenant_id: TenantId,
        template_id: ReportTemplateId,
        *,
        limit: int = 100,
        offset: int = 0,
    ) -> list[ReportRun]:
        stmt = (
            select(ReportRunModel)
            .where(
                ReportRunModel.tenant_id == tenant_id.value,
                ReportRunModel.template_id == template_id.value,
            )
            .order_by(ReportRunModel.created_at.desc())
            .limit(limit)
            .offset(offset)
        )
        rows = (await self._session.execute(stmt)).scalars().all()
        return [ReportRunMapper.to_entity(r) for r in rows]
