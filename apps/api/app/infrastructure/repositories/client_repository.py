"""
Client Repository Implementation

SQLAlchemy implementation of ClientRepository interface.
Uses TenantScopedRepositoryImpl base class to eliminate boilerplate.
"""

from collections.abc import Sequence
from typing import Any

from sqlalchemy import func, select

from app.domain.entities.client import ClientEntity
from app.domain.enums import BaseStatus, ClientTier
from app.domain.repositories.client_repository import ClientRepository
from app.domain.value_objects.core import ClientId, TenantId
from app.infrastructure.mappers.client_mapper import ClientMapper
from app.infrastructure.models.client_model import ClientModel
from app.infrastructure.repositories.base import TenantScopedRepositoryImpl


class ClientRepositoryImpl(
    TenantScopedRepositoryImpl[ClientEntity, ClientModel, ClientId], ClientRepository
):
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

    async def get_by_name(self, tenant_id: TenantId, name: str) -> ClientEntity | None:
        """Get client by name within tenant, excluding soft-deleted clients."""
        stmt = select(ClientModel).where(
            ClientModel.tenant_id == tenant_id.value,
            func.lower(ClientModel.name) == name.strip().lower(),
            ClientModel.deleted_at.is_(None),
        )
        result = await self.session.execute(stmt)
        model = result.scalar_one_or_none()

        if not model:
            return None

        return self._to_entity(model)

    async def get_by_code(self, tenant_id: TenantId, code: str) -> ClientEntity | None:
        """Get client by normalized code within tenant, excluding soft deletes."""
        stmt = select(ClientModel).where(
            ClientModel.tenant_id == tenant_id.value,
            func.upper(ClientModel.code) == code.strip().upper(),
            ClientModel.deleted_at.is_(None),
        )
        result = await self.session.execute(stmt)
        model = result.scalar_one_or_none()
        return self._to_entity(model) if model else None

    async def list_all(
        self,
        tenant_id: TenantId,
        status: BaseStatus | None = None,
        is_verified: bool | None = None,
        tier: "ClientTier | None" = None,
        search: str | None = None,
        limit: int = 100,
        offset: int = 0,
        sort_by: str = "created_at",
        sort_desc: bool = True,
    ) -> Sequence[ClientEntity]:
        """List clients with filtering, searching, and pagination."""
        filters: dict[str, Any] = {}
        if status:
            filters["status"] = status
        if is_verified is not None:
            filters["is_verified"] = is_verified
        if tier is not None:
            filters["tier"] = tier

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
        tier: "ClientTier | None" = None,
        search: str | None = None,
    ) -> int:
        """Count clients matching filters."""
        filters: dict[str, Any] = {}
        if status:
            filters["status"] = status
        if is_verified is not None:
            filters["is_verified"] = is_verified
        if tier is not None:
            filters["tier"] = tier

        return await self._count_all(
            tenant_id=tenant_id.value,
            filters=filters,
            search=search,
            search_fields=["name"],
        )
