"""ClientTag Repository Implementation - SQLAlchemy implementation."""

from typing import Any, Sequence

from sqlalchemy import select

from app.domain.entities.client_tag import ClientTagEntity
from app.domain.repositories.client_tag_repository import ClientTagRepository
from app.domain.value_objects.core import ClientTagId, TenantId
from app.infrastructure.mappers.client_tag_mapper import ClientTagMapper
from app.infrastructure.models.client_tag_model import ClientTagModel
from app.infrastructure.repositories.base import TenantScopedRepositoryImpl


class ClientTagRepositoryImpl(TenantScopedRepositoryImpl[ClientTagEntity, ClientTagModel, ClientTagId], ClientTagRepository):
    """
    SQLAlchemy implementation of ClientTagRepository.

    Inherits common CRUD operations from TenantScopedRepositoryImpl.
    Only implements domain-specific queries.
    """

    model_class = ClientTagModel
    id_column = "id"

    def _to_entity(self, model: ClientTagModel) -> ClientTagEntity:
        """Convert model to entity."""
        return ClientTagMapper.to_entity(model)

    def _to_model(self, entity: ClientTagEntity) -> ClientTagModel:
        """Convert entity to model."""
        return ClientTagMapper.to_model(entity)

    def _get_id_value(self, entity_id: ClientTagId) -> Any:
        """Extract raw ID value."""
        return entity_id.value

    # Domain-specific queries (not in base class)

    async def get_by_name(self, name: str, tenant_id: TenantId) -> ClientTagEntity | None:
        """Get tag by name within tenant."""
        stmt = select(ClientTagModel).where(
            ClientTagModel.name == name,
            ClientTagModel.tenant_id == tenant_id.value,
            ClientTagModel.deleted_at.is_(None),
        )
        result = await self.session.execute(stmt)
        model = result.scalar_one_or_none()
        return self._to_entity(model) if model else None

    async def list_all(
        self,
        tenant_id: TenantId,
        is_active: bool | None = None,
        search: str | None = None,
        limit: int = 100,
        offset: int = 0,
    ) -> Sequence[ClientTagEntity]:
        """List tags with filtering, searching, and pagination."""
        # Build filters dict for base class
        filters: dict[str, Any] = {}
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
        is_active: bool | None = None,
        search: str | None = None,
    ) -> int:
        """Count tags matching filters."""
        filters: dict[str, Any] = {}
        if is_active is not None:
            filters["is_active"] = is_active

        return await self._count_all(
            tenant_id=tenant_id.value,
            filters=filters,
            search=search,
            search_fields=["name"],
        )
