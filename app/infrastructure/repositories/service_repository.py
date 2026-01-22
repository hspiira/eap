"""
Service Repository Implementation

SQLAlchemy implementation of ServiceRepository interface.
"""

from typing import Sequence

from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.entities.service import ServiceEntity
from app.domain.enums import BaseStatus
from app.domain.repositories.service_repository import ServiceRepository
from app.domain.value_objects.core import ServiceId, TenantId
from app.infrastructure.mappers.service_mapper import ServiceMapper
from app.infrastructure.models.service_model import ServiceModel
from app.shared.utils.datetime import utc_now


class ServiceRepositoryImpl(ServiceRepository):
    """
    SQLAlchemy implementation of ServiceRepository.

    Handles data access for Service aggregate.
    Uses mapper to convert between entity and model.
    """

    def __init__(self, session: AsyncSession) -> None:
        """
        Initialize repository with database session.

        Args:
            session: SQLAlchemy async database session
        """
        self.session = session

    async def get_by_id(self, service_id: ServiceId) -> ServiceEntity | None:
        """Get service by ID, excluding soft-deleted services."""
        stmt = select(ServiceModel).where(
            ServiceModel.id == service_id.value,
            ServiceModel.deleted_at.is_(None),
        )
        result = await self.session.execute(stmt)
        model = result.scalar_one_or_none()

        if not model:
            return None

        return ServiceMapper.to_entity(model)

    async def get_by_name(
        self, tenant_id: TenantId, name: str
    ) -> ServiceEntity | None:
        """Get service by name within tenant, excluding soft-deleted services."""
        stmt = select(ServiceModel).where(
            ServiceModel.tenant_id == tenant_id.value,
            ServiceModel.name == name,
            ServiceModel.deleted_at.is_(None),
        )
        result = await self.session.execute(stmt)
        model = result.scalar_one_or_none()

        if not model:
            return None

        return ServiceMapper.to_entity(model)

    async def save(self, service: ServiceEntity) -> None:
        """
        Save service aggregate atomically.

        Uses merge to handle both insert and update.
        """
        model = ServiceMapper.to_model(service)
        await self.session.merge(model)
        # Note: commit is typically handled by the application service/unit of work

    async def delete(self, service_id: ServiceId) -> None:
        """
        Soft delete service.

        In practice, this is usually done by calling service.archive()
        and then save(), but this method provides explicit soft delete.
        """
        stmt = select(ServiceModel).where(
            ServiceModel.id == service_id.value,
            ServiceModel.deleted_at.is_(None),
        )
        result = await self.session.execute(stmt)
        model = result.scalar_one_or_none()

        if model:
            now = utc_now()
            model.deleted_at = now
            model.updated_at = now
            await self.session.merge(model)

    async def exists(self, service_id: ServiceId) -> bool:
        """Check if service exists (not soft-deleted)."""
        stmt = select(ServiceModel.id).where(
            ServiceModel.id == service_id.value,
            ServiceModel.deleted_at.is_(None),
        )
        result = await self.session.execute(stmt)
        return bool(result.scalar())

    async def list_all(
        self,
        tenant_id: TenantId,
        status: BaseStatus | None = None,
        category: str | None = None,
        is_group_service: bool | None = None,
        search: str | None = None,
        limit: int = 100,
        offset: int = 0,
        sort_by: str = "created_at",
        sort_desc: bool = True,
    ) -> Sequence[ServiceEntity]:
        """List services with filtering, searching, and pagination."""
        stmt = select(ServiceModel).where(
            ServiceModel.tenant_id == tenant_id.value,
            ServiceModel.deleted_at.is_(None),
        )

        # Apply filters
        if status:
            stmt = stmt.where(ServiceModel.status == status)
        if category:
            stmt = stmt.where(ServiceModel.category == category)
        if is_group_service is not None:
            stmt = stmt.where(ServiceModel.is_group_service == is_group_service)
        if search:
            search_pattern = f"%{search.lower()}%"
            stmt = stmt.where(
                or_(
                    ServiceModel.name.ilike(search_pattern),
                    ServiceModel.description.ilike(search_pattern),
                )
            )

        # Apply sorting
        sort_column = getattr(ServiceModel, sort_by, ServiceModel.created_at)
        if sort_desc:
            stmt = stmt.order_by(sort_column.desc())
        else:
            stmt = stmt.order_by(sort_column.asc())

        # Apply pagination
        stmt = stmt.limit(limit).offset(offset)

        result = await self.session.execute(stmt)
        models = result.scalars().all()

        return [ServiceMapper.to_entity(model) for model in models]

    async def count(
        self,
        tenant_id: TenantId,
        status: BaseStatus | None = None,
        category: str | None = None,
        is_group_service: bool | None = None,
        search: str | None = None,
    ) -> int:
        """Count services matching filters."""
        stmt = select(func.count(ServiceModel.id)).where(
            ServiceModel.tenant_id == tenant_id.value,
            ServiceModel.deleted_at.is_(None),
        )

        # Apply filters
        if status:
            stmt = stmt.where(ServiceModel.status == status)
        if category:
            stmt = stmt.where(ServiceModel.category == category)
        if is_group_service is not None:
            stmt = stmt.where(ServiceModel.is_group_service == is_group_service)
        if search:
            search_pattern = f"%{search.lower()}%"
            stmt = stmt.where(
                or_(
                    ServiceModel.name.ilike(search_pattern),
                    ServiceModel.description.ilike(search_pattern),
                )
            )

        result = await self.session.execute(stmt)
        return int(result.scalar() or 0)
