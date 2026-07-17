"""Industry Repository Implementation - SQLAlchemy implementation."""

from collections.abc import Sequence
from typing import Any

from sqlalchemy import select

from app.domain.entities.industry import IndustryEntity
from app.domain.repositories.industry_repository import IndustryRepository
from app.domain.value_objects.core import IndustryId, TenantId
from app.infrastructure.mappers.industry_mapper import IndustryMapper
from app.infrastructure.models.industry_model import IndustryModel
from app.infrastructure.repositories.base import TenantScopedRepositoryImpl


class IndustryRepositoryImpl(
    TenantScopedRepositoryImpl[IndustryEntity, IndustryModel, IndustryId], IndustryRepository
):
    """
    SQLAlchemy implementation of IndustryRepository.

    Inherits common CRUD operations from TenantScopedRepositoryImpl.
    Only implements domain-specific queries.
    """

    model_class = IndustryModel
    id_column = "id"

    def _to_entity(self, model: IndustryModel) -> IndustryEntity:
        """Convert model to entity."""
        return IndustryMapper.to_entity(model)

    def _to_model(self, entity: IndustryEntity) -> IndustryModel:
        """Convert entity to model."""
        return IndustryMapper.to_model(entity)

    def _get_id_value(self, entity_id: IndustryId) -> Any:
        """Extract raw ID value."""
        return entity_id.value

    # Domain-specific queries (not in base class)

    async def get_by_name(self, name: str, tenant_id: TenantId) -> IndustryEntity | None:
        """Get industry by name within tenant."""
        stmt = select(IndustryModel).where(
            IndustryModel.name == name,
            IndustryModel.tenant_id == tenant_id.value,
            IndustryModel.deleted_at.is_(None),
        )
        result = await self.session.execute(stmt)
        model = result.scalar_one_or_none()
        return self._to_entity(model) if model else None

    async def get_by_code(self, code: str, tenant_id: TenantId) -> IndustryEntity | None:
        """Get industry by code within tenant."""
        stmt = select(IndustryModel).where(
            IndustryModel.code == code,
            IndustryModel.tenant_id == tenant_id.value,
            IndustryModel.deleted_at.is_(None),
        )
        result = await self.session.execute(stmt)
        model = result.scalar_one_or_none()
        return self._to_entity(model) if model else None

    async def get_children(
        self, parent_id: IndustryId, tenant_id: TenantId
    ) -> Sequence[IndustryEntity]:
        """Get all child industries of a parent."""
        stmt = select(IndustryModel).where(
            IndustryModel.parent_industry_id == parent_id.value,
            IndustryModel.tenant_id == tenant_id.value,
            IndustryModel.deleted_at.is_(None),
        )
        result = await self.session.execute(stmt)
        models = result.scalars().all()
        return [self._to_entity(m) for m in models]

    async def list_all(
        self,
        tenant_id: TenantId,
        parent_id: IndustryId | None = None,
        is_active: bool | None = None,
        search: str | None = None,
        limit: int = 100,
        offset: int = 0,
    ) -> Sequence[IndustryEntity]:
        """List industries with filtering, searching, and pagination."""
        # Build filters dict for base class
        filters: dict[str, Any] = {}
        if parent_id:
            filters["parent_industry_id"] = parent_id.value
        if is_active is not None:
            filters["is_active"] = is_active

        return await self._query_all(
            tenant_id=tenant_id.value,
            limit=limit,
            offset=offset,
            sort_by="name",
            sort_desc=False,
            filters=filters,
            search=search,
            search_fields=["name"],
        )

    async def count(
        self,
        tenant_id: TenantId,
        parent_id: IndustryId | None = None,
        is_active: bool | None = None,
        search: str | None = None,
    ) -> int:
        """Count industries matching filters."""
        filters: dict[str, Any] = {}
        if parent_id:
            filters["parent_industry_id"] = parent_id.value
        if is_active is not None:
            filters["is_active"] = is_active

        return await self._count_all(
            tenant_id=tenant_id.value,
            filters=filters,
            search=search,
            search_fields=["name"],
        )
