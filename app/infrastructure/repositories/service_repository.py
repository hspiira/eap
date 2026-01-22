"""
Service Repository Implementation

SQLAlchemy implementation of ServiceRepository interface.
Uses TenantScopedRepositoryImpl base class to eliminate boilerplate.
"""

from typing import Any, Sequence

from sqlalchemy import select

from app.domain.entities.service import ServiceEntity
from app.domain.enums import BaseStatus
from app.domain.repositories.service_repository import ServiceRepository
from app.domain.value_objects.core import ServiceId, TenantId
from app.infrastructure.mappers.service_mapper import ServiceMapper
from app.infrastructure.models.service_model import ServiceModel
from app.infrastructure.repositories.base import TenantScopedRepositoryImpl


class ServiceRepositoryImpl(TenantScopedRepositoryImpl[ServiceEntity, ServiceModel, ServiceId], ServiceRepository):
    """
    SQLAlchemy implementation of ServiceRepository.

    Inherits common CRUD operations from TenantScopedRepositoryImpl.
    Only implements domain-specific queries.
    """

    model_class = ServiceModel
    id_column = "id"

    def _to_entity(self, model: ServiceModel) -> ServiceEntity:
        """Convert model to entity."""
        return ServiceMapper.to_entity(model)

    def _to_model(self, entity: ServiceEntity) -> ServiceModel:
        """Convert entity to model."""
        return ServiceMapper.to_model(entity)

    def _get_id_value(self, entity_id: ServiceId) -> Any:
        """Extract raw ID value."""
        return entity_id.value

    # Domain-specific queries (not in base class)

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

        return self._to_entity(model)

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
        # Build filters dict for base class
        filters: dict[str, Any] = {}
        if status:
            filters["status"] = status
        if category:
            filters["category"] = category
        if is_group_service is not None:
            filters["is_group_service"] = is_group_service

        return await self._query_all(
            tenant_id=tenant_id.value,
            limit=limit,
            offset=offset,
            sort_by=sort_by,
            sort_desc=sort_desc,
            filters=filters,
            search=search,
            search_fields=["name", "description"],
        )

    async def count(
        self,
        tenant_id: TenantId,
        status: BaseStatus | None = None,
        category: str | None = None,
        is_group_service: bool | None = None,
        search: str | None = None,
    ) -> int:
        """Count services matching filters."""
        filters: dict[str, Any] = {}
        if status:
            filters["status"] = status
        if category:
            filters["category"] = category
        if is_group_service is not None:
            filters["is_group_service"] = is_group_service

        return await self._count_all(
            tenant_id=tenant_id.value,
            filters=filters,
            search=search,
            search_fields=["name", "description"],
        )
