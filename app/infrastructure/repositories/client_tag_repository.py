"""ClientTag Repository Implementation - SQLAlchemy implementation."""

from typing import Sequence

from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.entities.client_tag import ClientTagEntity
from app.domain.repositories.client_tag_repository import ClientTagRepository
from app.domain.value_objects.core import ClientTagId, TenantId
from app.infrastructure.mappers.client_tag_mapper import ClientTagMapper
from app.infrastructure.models.client_tag_model import ClientTagModel
from app.shared.utils.datetime import utc_now


class ClientTagRepositoryImpl(ClientTagRepository):
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def get_by_id(self, tag_id: ClientTagId) -> ClientTagEntity | None:
        stmt = select(ClientTagModel).where(
            ClientTagModel.id == tag_id.value,
            ClientTagModel.deleted_at.is_(None),
        )
        result = await self.session.execute(stmt)
        model = result.scalar_one_or_none()
        return ClientTagMapper.to_entity(model) if model else None

    async def get_by_name(self, name: str, tenant_id: TenantId) -> ClientTagEntity | None:
        stmt = select(ClientTagModel).where(
            ClientTagModel.name == name,
            ClientTagModel.tenant_id == tenant_id.value,
            ClientTagModel.deleted_at.is_(None),
        )
        result = await self.session.execute(stmt)
        model = result.scalar_one_or_none()
        return ClientTagMapper.to_entity(model) if model else None

    async def list_all(
        self,
        tenant_id: TenantId,
        is_active: bool | None = None,
        search: str | None = None,
        limit: int = 100,
        offset: int = 0,
    ) -> Sequence[ClientTagEntity]:
        stmt = select(ClientTagModel).where(
            ClientTagModel.tenant_id == tenant_id.value,
            ClientTagModel.deleted_at.is_(None),
        )
        if is_active is not None:
            stmt = stmt.where(ClientTagModel.is_active == is_active)
        if search:
            stmt = stmt.where(ClientTagModel.name.ilike(f"%{search}%"))
        stmt = stmt.limit(limit).offset(offset).order_by(ClientTagModel.name)
        result = await self.session.execute(stmt)
        return [ClientTagMapper.to_entity(m) for m in result.scalars().all()]

    async def count(
        self,
        tenant_id: TenantId,
        is_active: bool | None = None,
        search: str | None = None,
    ) -> int:
        stmt = select(func.count(ClientTagModel.id)).where(
            ClientTagModel.tenant_id == tenant_id.value,
            ClientTagModel.deleted_at.is_(None),
        )
        if is_active is not None:
            stmt = stmt.where(ClientTagModel.is_active == is_active)
        if search:
            stmt = stmt.where(ClientTagModel.name.ilike(f"%{search}%"))
        result = await self.session.execute(stmt)
        return int(result.scalar() or 0)

    async def save(self, tag: ClientTagEntity) -> None:
        model = ClientTagMapper.to_model(tag)
        await self.session.merge(model)

    async def delete(self, tag_id: ClientTagId) -> None:
        stmt = select(ClientTagModel).where(
            ClientTagModel.id == tag_id.value,
            ClientTagModel.deleted_at.is_(None),
        )
        result = await self.session.execute(stmt)
        model = result.scalar_one_or_none()
        if model:
            model.deleted_at = utc_now()
            model.updated_at = utc_now()
            await self.session.merge(model)

    async def exists(self, tag_id: ClientTagId) -> bool:
        from sqlalchemy import exists as sql_exists
        stmt = sql_exists().where(
            ClientTagModel.id == tag_id.value,
            ClientTagModel.deleted_at.is_(None),
        ).select()
        result = await self.session.execute(stmt)
        return bool(result.scalar())
