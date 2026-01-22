"""
Client Repository Implementation

SQLAlchemy implementation of ClientRepository interface.
Uses TenantScopedRepositoryImpl base class to eliminate boilerplate.
"""

from typing import Any, Sequence

from sqlalchemy import select

from app.domain.entities.client import ClientEntity
from app.domain.enums import BaseStatus
from app.domain.repositories.client_repository import ClientRepository
from app.domain.value_objects.core import ClientId, TenantId
from app.infrastructure.mappers.client_mapper import ClientMapper
from app.infrastructure.models.client_model import ClientModel
from app.infrastructure.repositories.base import TenantScopedRepositoryImpl


class ClientRepositoryImpl(TenantScopedRepositoryImpl[ClientEntity, ClientModel, ClientId], ClientRepository):
    """
    SQLAlchemy implementation of ClientRepository.

    Inherits common CRUD operations from TenantScopedRepositoryImpl.
    Only implements domain-specific queries.
    """

    model_class = ClientModel
    id_column = "id"

    def _to_entity(self, model: ClientModel) -> ClientEntity:
        """Convert model to entity."""
        return ClientMapper.to_entity(model)

    def _to_model(self, entity: ClientEntity) -> ClientModel:
        """Convert entity to model."""
        return ClientMapper.to_model(entity)

    def _get_id_value(self, entity_id: ClientId) -> Any:
        """Extract raw ID value."""
        return entity_id.value

    # Domain-specific queries (not in base class)

    async def get_by_name(
        self, tenant_id: TenantId, name: str
    ) -> ClientEntity | None:
        """Get client by name within tenant, excluding soft-deleted clients."""
        stmt = select(ClientModel).where(
            ClientModel.tenant_id == tenant_id.value,
            ClientModel.name == name,
            ClientModel.deleted_at.is_(None),
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
        is_verified: bool | None = None,
        search: str | None = None,
        limit: int = 100,
        offset: int = 0,
        sort_by: str = "created_at",
        sort_desc: bool = True,
    ) -> Sequence[ClientEntity]:
        """List clients with filtering, searching, and pagination."""
        # Build filters dict for base class
        filters: dict[str, Any] = {}
        if status:
            filters["status"] = status
        if is_verified is not None:
            filters["is_verified"] = is_verified

        return await self._query_all(
            tenant_id=tenant_id.value,
            limit=limit,
            offset=offset,
            sort_by=sort_by,
            sort_desc=sort_desc,
            filters=filters,
            search=search,
            search_fields=["name"],
        )

    async def count(
        self,
        tenant_id: TenantId,
        status: BaseStatus | None = None,
        is_verified: bool | None = None,
        search: str | None = None,
    ) -> int:
        """Count clients matching filters."""
        filters: dict[str, Any] = {}
        if status:
            filters["status"] = status
        if is_verified is not None:
            filters["is_verified"] = is_verified

        return await self._count_all(
            tenant_id=tenant_id.value,
            filters=filters,
            search=search,
            search_fields=["name"],
        )
