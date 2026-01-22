"""Activity Repository Implementation - SQLAlchemy implementation."""

from datetime import datetime
from typing import Sequence

from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.entities.activity import ActivityEntity
from app.domain.repositories.activity_repository import ActivityRepository
from app.domain.value_objects.core import ActivityId, TenantId
from app.infrastructure.mappers.activity_mapper import ActivityMapper
from app.infrastructure.models.activity_model import ActivityModel
from app.shared.utils.datetime import utc_now


class ActivityRepositoryImpl(ActivityRepository):
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def get_by_id(self, activity_id: ActivityId) -> ActivityEntity | None:
        stmt = select(ActivityModel).where(
            ActivityModel.id == activity_id.value,
            ActivityModel.deleted_at.is_(None),
        )
        result = await self.session.execute(stmt)
        model = result.scalar_one_or_none()
        return ActivityMapper.to_entity(model) if model else None

    async def get_by_client_id(self, client_id: str, tenant_id: TenantId) -> Sequence[ActivityEntity]:
        stmt = select(ActivityModel).where(
            ActivityModel.client_id == client_id,
            ActivityModel.tenant_id == tenant_id.value,
            ActivityModel.deleted_at.is_(None),
        ).order_by(ActivityModel.occurred_at.desc())
        result = await self.session.execute(stmt)
        models = result.scalars().all()
        return [ActivityMapper.to_entity(m) for m in models]

    async def list_all(
        self,
        tenant_id: TenantId,
        client_id: str | None = None,
        activity_type: str | None = None,
        created_by: str | None = None,
        date_from: datetime | None = None,
        date_to: datetime | None = None,
        is_important: bool | None = None,
        search: str | None = None,
        limit: int = 100,
        offset: int = 0,
    ) -> Sequence[ActivityEntity]:
        stmt = select(ActivityModel).where(
            ActivityModel.tenant_id == tenant_id.value,
            ActivityModel.deleted_at.is_(None),
        )
        if client_id:
            stmt = stmt.where(ActivityModel.client_id == client_id)
        if activity_type:
            stmt = stmt.where(ActivityModel.activity_type == activity_type)
        if created_by:
            stmt = stmt.where(ActivityModel.created_by == created_by)
        if date_from:
            stmt = stmt.where(ActivityModel.occurred_at >= date_from)
        if date_to:
            stmt = stmt.where(ActivityModel.occurred_at <= date_to)
        if is_important is not None:
            stmt = stmt.where(ActivityModel.is_important == is_important)
        if search:
            stmt = stmt.where(
                or_(
                    ActivityModel.description.ilike(f"%{search}%"),
                    ActivityModel.subject.ilike(f"%{search}%"),
                )
            )
        stmt = stmt.order_by(ActivityModel.occurred_at.desc()).limit(limit).offset(offset)
        result = await self.session.execute(stmt)
        return [ActivityMapper.to_entity(m) for m in result.scalars().all()]

    async def count(
        self,
        tenant_id: TenantId,
        client_id: str | None = None,
        activity_type: str | None = None,
        created_by: str | None = None,
        date_from: datetime | None = None,
        date_to: datetime | None = None,
        is_important: bool | None = None,
        search: str | None = None,
    ) -> int:
        stmt = select(func.count(ActivityModel.id)).where(
            ActivityModel.tenant_id == tenant_id.value,
            ActivityModel.deleted_at.is_(None),
        )
        if client_id:
            stmt = stmt.where(ActivityModel.client_id == client_id)
        if activity_type:
            stmt = stmt.where(ActivityModel.activity_type == activity_type)
        if created_by:
            stmt = stmt.where(ActivityModel.created_by == created_by)
        if date_from:
            stmt = stmt.where(ActivityModel.occurred_at >= date_from)
        if date_to:
            stmt = stmt.where(ActivityModel.occurred_at <= date_to)
        if is_important is not None:
            stmt = stmt.where(ActivityModel.is_important == is_important)
        if search:
            stmt = stmt.where(
                or_(
                    ActivityModel.description.ilike(f"%{search}%"),
                    ActivityModel.subject.ilike(f"%{search}%"),
                )
            )
        result = await self.session.execute(stmt)
        return int(result.scalar() or 0)

    async def save(self, activity: ActivityEntity) -> None:
        model = ActivityMapper.to_model(activity)
        await self.session.merge(model)

    async def delete(self, activity_id: ActivityId) -> None:
        stmt = select(ActivityModel).where(
            ActivityModel.id == activity_id.value,
            ActivityModel.deleted_at.is_(None),
        )
        result = await self.session.execute(stmt)
        model = result.scalar_one_or_none()
        if model:
            model.deleted_at = utc_now()
            model.updated_at = utc_now()
            await self.session.merge(model)

    async def exists(self, activity_id: ActivityId) -> bool:
        from sqlalchemy import exists as sql_exists
        stmt = sql_exists().where(
            ActivityModel.id == activity_id.value,
            ActivityModel.deleted_at.is_(None),
        ).select()
        result = await self.session.execute(stmt)
        return bool(result.scalar())
