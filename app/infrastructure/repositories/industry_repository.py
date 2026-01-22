"""Industry Repository Implementation - SQLAlchemy implementation."""

from typing import Sequence

from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.entities.industry import IndustryEntity
from app.domain.repositories.industry_repository import IndustryRepository
from app.domain.value_objects.core import IndustryId, TenantId
from app.infrastructure.mappers.industry_mapper import IndustryMapper
from app.infrastructure.models.industry_model import IndustryModel
from app.shared.utils.datetime import utc_now


class IndustryRepositoryImpl(IndustryRepository):
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def get_by_id(self, industry_id: IndustryId) -> IndustryEntity | None:
        stmt = select(IndustryModel).where(
            IndustryModel.id == industry_id.value,
            IndustryModel.deleted_at.is_(None),
        )
        result = await self.session.execute(stmt)
        model = result.scalar_one_or_none()
        return IndustryMapper.to_entity(model) if model else None

    async def get_by_name(self, name: str, tenant_id: TenantId) -> IndustryEntity | None:
        stmt = select(IndustryModel).where(
            IndustryModel.name == name,
            IndustryModel.tenant_id == tenant_id.value,
            IndustryModel.deleted_at.is_(None),
        )
        result = await self.session.execute(stmt)
        model = result.scalar_one_or_none()
        return IndustryMapper.to_entity(model) if model else None

    async def get_children(self, parent_id: IndustryId, tenant_id: TenantId) -> Sequence[IndustryEntity]:
        stmt = select(IndustryModel).where(
            IndustryModel.parent_industry_id == parent_id.value,
            IndustryModel.tenant_id == tenant_id.value,
            IndustryModel.deleted_at.is_(None),
        )
        result = await self.session.execute(stmt)
        models = result.scalars().all()
        return [IndustryMapper.to_entity(m) for m in models]

    async def list_all(
        self,
        tenant_id: TenantId,
        parent_id: IndustryId | None = None,
        is_active: bool | None = None,
        search: str | None = None,
        limit: int = 100,
        offset: int = 0,
    ) -> Sequence[IndustryEntity]:
        stmt = select(IndustryModel).where(
            IndustryModel.tenant_id == tenant_id.value,
            IndustryModel.deleted_at.is_(None),
        )
        if parent_id:
            stmt = stmt.where(IndustryModel.parent_industry_id == parent_id.value)
        if is_active is not None:
            stmt = stmt.where(IndustryModel.is_active == is_active)
        if search:
            stmt = stmt.where(IndustryModel.name.ilike(f"%{search}%"))
        stmt = stmt.limit(limit).offset(offset).order_by(IndustryModel.name)
        result = await self.session.execute(stmt)
        return [IndustryMapper.to_entity(m) for m in result.scalars().all()]

    async def count(
        self,
        tenant_id: TenantId,
        parent_id: IndustryId | None = None,
        is_active: bool | None = None,
        search: str | None = None,
    ) -> int:
        stmt = select(func.count(IndustryModel.id)).where(
            IndustryModel.tenant_id == tenant_id.value,
            IndustryModel.deleted_at.is_(None),
        )
        if parent_id:
            stmt = stmt.where(IndustryModel.parent_industry_id == parent_id.value)
        if is_active is not None:
            stmt = stmt.where(IndustryModel.is_active == is_active)
        if search:
            stmt = stmt.where(IndustryModel.name.ilike(f"%{search}%"))
        result = await self.session.execute(stmt)
        return int(result.scalar() or 0)

    async def save(self, industry: IndustryEntity) -> None:
        model = IndustryMapper.to_model(industry)
        await self.session.merge(model)

    async def delete(self, industry_id: IndustryId) -> None:
        stmt = select(IndustryModel).where(
            IndustryModel.id == industry_id.value,
            IndustryModel.deleted_at.is_(None),
        )
        result = await self.session.execute(stmt)
        model = result.scalar_one_or_none()
        if model:
            model.deleted_at = utc_now()
            model.updated_at = utc_now()
            await self.session.merge(model)

    async def exists(self, industry_id: IndustryId) -> bool:
        from sqlalchemy import exists as sql_exists
        stmt = sql_exists().where(
            IndustryModel.id == industry_id.value,
            IndustryModel.deleted_at.is_(None),
        ).select()
        result = await self.session.execute(stmt)
        return bool(result.scalar())
