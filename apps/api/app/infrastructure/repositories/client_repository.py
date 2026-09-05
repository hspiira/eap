"""
Client Repository Implementation

SQLAlchemy implementation of ClientRepository interface.
Uses TenantScopedRepositoryImpl base class to eliminate boilerplate.
"""

from collections.abc import Sequence
from typing import Any

from sqlalchemy import func, or_, select

from app.domain.entities.client import ClientEntity
from app.domain.enums import BaseStatus, ClientTier
from app.domain.repositories.client_repository import ClientRepository
from app.domain.value_objects.core import ClientId, TenantId
from app.infrastructure.mappers.client_mapper import ClientMapper
from app.infrastructure.models.client_alias_model import ClientAliasModel
from app.infrastructure.models.client_model import ClientModel
from app.infrastructure.repositories.base import TenantScopedRepositoryImpl
from app.shared.utils.client_alias import normalize_client_alias


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

    async def get_by_name_or_alias(self, tenant_id: TenantId, value: str) -> ClientEntity | None:
        """Resolve a canonical client name or a tenant-scoped alias."""
        client = await self.get_by_name(tenant_id, value)
        if client:
            return client
        normalized = normalize_client_alias(value)
        stmt = (
            select(ClientModel)
            .join(ClientAliasModel, ClientAliasModel.client_id == ClientModel.id)
            .where(
                ClientModel.tenant_id == tenant_id.value,
                ClientModel.deleted_at.is_(None),
                ClientAliasModel.normalized_alias == normalized,
            )
        )
        result = await self.session.execute(stmt)
        model = result.scalar_one_or_none()
        if model:
            return self._to_entity(model)
        if len(normalized) < 4:
            return None
        prefix_result = await self.session.execute(
            select(ClientModel)
            .join(ClientAliasModel, ClientAliasModel.client_id == ClientModel.id)
            .where(
                ClientModel.tenant_id == tenant_id.value,
                ClientModel.deleted_at.is_(None),
                ClientAliasModel.normalized_alias.like(f"{normalized}%"),
            )
        )
        models = prefix_result.unique().scalars().all()
        return self._to_entity(models[0]) if len(models) == 1 else None

    async def list_all(
        self,
        tenant_id: TenantId,
        status: BaseStatus | None = None,
        is_verified: bool | None = None,
        tier: "ClientTier | None" = None,
        parent_client_id: ClientId | None = None,
        include_archived: bool = False,
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
        if parent_client_id is not None:
            filters["parent_client_id"] = parent_client_id.value

        extra_conditions = []
        if not include_archived and status is None:
            extra_conditions.append(ClientModel.status != BaseStatus.ARCHIVED)
        if search:
            extra_conditions.append(
                or_(
                    ClientModel.name.ilike(f"%{search}%"),
                    ClientModel.id.in_(
                        select(ClientAliasModel.client_id).where(
                            ClientAliasModel.tenant_id == tenant_id.value,
                            ClientAliasModel.alias.ilike(f"%{search}%"),
                        )
                    ),
                )
            )

        return await self._query_all(
            tenant_id=tenant_id.value,
            limit=limit,
            offset=offset,
            sort_by=sort_by,
            sort_desc=sort_desc,
            filters=filters,
            search=None,
            search_fields=["name"],
            extra_conditions=extra_conditions,
        )

    async def count(
        self,
        tenant_id: TenantId,
        status: BaseStatus | None = None,
        is_verified: bool | None = None,
        tier: "ClientTier | None" = None,
        parent_client_id: ClientId | None = None,
        include_archived: bool = False,
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
        if parent_client_id is not None:
            filters["parent_client_id"] = parent_client_id.value

        extra_conditions = []
        if not include_archived and status is None:
            extra_conditions.append(ClientModel.status != BaseStatus.ARCHIVED)
        if search:
            extra_conditions.append(
                or_(
                    ClientModel.name.ilike(f"%{search}%"),
                    ClientModel.id.in_(
                        select(ClientAliasModel.client_id).where(
                            ClientAliasModel.tenant_id == tenant_id.value,
                            ClientAliasModel.alias.ilike(f"%{search}%"),
                        )
                    ),
                )
            )

        return await self._count_all(
            tenant_id=tenant_id.value,
            filters=filters,
            search=None,
            search_fields=["name"],
            extra_conditions=extra_conditions,
        )
