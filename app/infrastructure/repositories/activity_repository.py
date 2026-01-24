"""Activity Repository Implementation - SQLAlchemy implementation."""

from collections.abc import Sequence
from datetime import datetime
from typing import Any

from sqlalchemy import func, or_, select

from app.domain.entities.activity import ActivityEntity
from app.domain.repositories.activity_repository import ActivityRepository
from app.domain.value_objects.core import ActivityId, TenantId
from app.infrastructure.mappers.activity_mapper import ActivityMapper
from app.infrastructure.models.activity_model import ActivityModel
from app.infrastructure.repositories.base import TenantScopedRepositoryImpl


class ActivityRepositoryImpl(TenantScopedRepositoryImpl[ActivityEntity, ActivityModel, ActivityId], ActivityRepository):
    """
    SQLAlchemy implementation of ActivityRepository.

    Inherits common CRUD operations from TenantScopedRepositoryImpl.
    Only implements domain-specific queries.
    """

    model_class = ActivityModel
    id_column = "id"

    def _to_entity(self, model: ActivityModel) -> ActivityEntity:
        """Convert model to entity."""
        return ActivityMapper.to_entity(model)

    def _to_model(self, entity: ActivityEntity) -> ActivityModel:
        """Convert entity to model."""
        return ActivityMapper.to_model(entity)

    def _get_id_value(self, entity_id: ActivityId) -> Any:
        """Extract raw ID value."""
        return entity_id.value

    # Domain-specific queries (not in base class)

    async def get_by_client_id(self, client_id: str, tenant_id: TenantId) -> Sequence[ActivityEntity]:
        """Get all activities for a client."""
        stmt = select(ActivityModel).where(
            ActivityModel.client_id == client_id,
            ActivityModel.tenant_id == tenant_id.value,
            ActivityModel.deleted_at.is_(None),
        ).order_by(ActivityModel.occurred_at.desc())
        result = await self.session.execute(stmt)
        models = result.scalars().all()
        return [self._to_entity(m) for m in models]

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
        """List activities with filtering, searching, and pagination."""
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
        return [self._to_entity(m) for m in result.scalars().all()]

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
        """Count activities matching filters."""
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
