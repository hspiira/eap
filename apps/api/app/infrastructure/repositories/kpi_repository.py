"""
KPI Repository Implementation

SQLAlchemy implementation of KPI repository interfaces.
Uses TenantScopedRepositoryImpl base class to eliminate boilerplate.
"""

from collections.abc import Sequence
from typing import Any

from sqlalchemy import select

from app.domain.entities.kpi import KPIAssignmentEntity, KPIEntity
from app.domain.repositories.kpi_repository import (
    KPIAssignmentRepository,
    KPIRepository,
)
from app.domain.value_objects.core import KPIAssignmentId, KPIId, TenantId
from app.infrastructure.mappers.kpi_mapper import (
    KPIAssignmentMapper,
    KPIMapper,
)
from app.infrastructure.models.kpi_model import (
    KPIAssignmentModel,
    KPIModel,
)
from app.infrastructure.repositories.base import TenantScopedRepositoryImpl


class KPIRepositoryImpl(TenantScopedRepositoryImpl[KPIEntity, KPIModel, KPIId], KPIRepository):
    """
    SQLAlchemy implementation of KPIRepository.

    Inherits common CRUD operations from TenantScopedRepositoryImpl.
    Only implements domain-specific queries.
    """

    model_class = KPIModel
    id_column = "id"

    def _to_entity(self, model: KPIModel) -> KPIEntity:
        """Convert model to entity."""
        return KPIMapper.to_entity(model)

    def _to_model(self, entity: KPIEntity) -> KPIModel:
        """Convert entity to model."""
        return KPIMapper.to_model(entity)

    def _get_id_value(self, entity_id: KPIId) -> Any:
        """Extract raw ID value."""
        return entity_id.value

    async def get_by_name(self, name: str, tenant_id: TenantId) -> KPIEntity | None:
        """Get KPI by name within tenant, excluding soft-deleted KPIs."""
        stmt = select(KPIModel).where(
            KPIModel.name == name,
            KPIModel.tenant_id == tenant_id.value,
            KPIModel.deleted_at.is_(None),
        )
        result = await self.session.execute(stmt)
        model = result.scalar_one_or_none()
        if not model:
            return None
        return self._to_entity(model)

    async def list_all(
        self,
        tenant_id: TenantId,
        category: str | None = None,
        is_active: bool | None = None,
        search: str | None = None,
        limit: int = 100,
        offset: int = 0,
        sort_by: str = "created_at",
        sort_desc: bool = True,
    ) -> Sequence[KPIEntity]:
        """List KPIs with filtering, searching, and pagination."""
        # Build filters dict for base class
        filters: dict[str, Any] = {}
        if category:
            filters["category"] = category
        if is_active is not None:
            filters["is_active"] = is_active

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
        category: str | None = None,
        is_active: bool | None = None,
        search: str | None = None,
    ) -> int:
        """Count KPIs matching filters."""
        filters: dict[str, Any] = {}
        if category:
            filters["category"] = category
        if is_active is not None:
            filters["is_active"] = is_active

        return await self._count_all(
            tenant_id=tenant_id.value,
            filters=filters,
            search=search,
            search_fields=["name", "description"],
        )


class KPIAssignmentRepositoryImpl(
    TenantScopedRepositoryImpl[KPIAssignmentEntity, KPIAssignmentModel, KPIAssignmentId],
    KPIAssignmentRepository,
):
    """
    SQLAlchemy implementation of KPIAssignmentRepository.

    Inherits common CRUD operations from TenantScopedRepositoryImpl.
    Only implements domain-specific queries.
    """

    model_class = KPIAssignmentModel
    id_column = "id"

    def _to_entity(self, model: KPIAssignmentModel) -> KPIAssignmentEntity:
        """Convert model to entity."""
        return KPIAssignmentMapper.to_entity(model)

    def _to_model(self, entity: KPIAssignmentEntity) -> KPIAssignmentModel:
        """Convert entity to model."""
        return KPIAssignmentMapper.to_model(entity)

    def _get_id_value(self, entity_id: KPIAssignmentId) -> Any:
        """Extract raw ID value."""
        return entity_id.value

    # Domain-specific queries (not in base class)

    async def get_by_kpi_id(
        self, kpi_id: KPIId, tenant_id: TenantId
    ) -> Sequence[KPIAssignmentEntity]:
        """Get all assignments for a KPI."""
        stmt = select(KPIAssignmentModel).where(
            KPIAssignmentModel.kpi_id == kpi_id.value,
            KPIAssignmentModel.tenant_id == tenant_id.value,
            KPIAssignmentModel.deleted_at.is_(None),
        )
        result = await self.session.execute(stmt)
        models = result.scalars().all()

        return [self._to_entity(model) for model in models]

    async def get_by_client_id(
        self, client_id: str, tenant_id: TenantId
    ) -> Sequence[KPIAssignmentEntity]:
        """Get all assignments for a client."""
        stmt = select(KPIAssignmentModel).where(
            KPIAssignmentModel.client_id == client_id,
            KPIAssignmentModel.tenant_id == tenant_id.value,
            KPIAssignmentModel.deleted_at.is_(None),
        )
        result = await self.session.execute(stmt)
        models = result.scalars().all()

        return [self._to_entity(model) for model in models]

    async def get_by_contract_id(
        self, contract_id: str, tenant_id: TenantId
    ) -> Sequence[KPIAssignmentEntity]:
        """Get all assignments for a contract."""
        stmt = select(KPIAssignmentModel).where(
            KPIAssignmentModel.contract_id == contract_id,
            KPIAssignmentModel.tenant_id == tenant_id.value,
            KPIAssignmentModel.deleted_at.is_(None),
        )
        result = await self.session.execute(stmt)
        models = result.scalars().all()

        return [self._to_entity(model) for model in models]

    async def list_all(
        self,
        tenant_id: TenantId,
        kpi_id: KPIId | None = None,
        client_id: str | None = None,
        contract_id: str | None = None,
        is_active: bool | None = None,
        limit: int = 100,
        offset: int = 0,
        sort_by: str = "created_at",
        sort_desc: bool = True,
    ) -> Sequence[KPIAssignmentEntity]:
        """List assignments with filtering and pagination."""
        # Build filters dict for base class
        filters: dict[str, Any] = {}
        if kpi_id:
            filters["kpi_id"] = kpi_id.value
        if client_id:
            filters["client_id"] = client_id
        if contract_id:
            filters["contract_id"] = contract_id
        if is_active is not None:
            filters["is_active"] = is_active

        return await self._query_all(
            tenant_id=tenant_id.value,
            limit=limit,
            offset=offset,
            sort_by=sort_by,
            sort_desc=sort_desc,
            filters=filters,
            search=None,
            search_fields=None,
        )

    async def count(
        self,
        tenant_id: TenantId,
        kpi_id: KPIId | None = None,
        client_id: str | None = None,
        contract_id: str | None = None,
        is_active: bool | None = None,
    ) -> int:
        """Count assignments matching filters."""
        filters: dict[str, Any] = {}
        if kpi_id:
            filters["kpi_id"] = kpi_id.value
        if client_id:
            filters["client_id"] = client_id
        if contract_id:
            filters["contract_id"] = contract_id
        if is_active is not None:
            filters["is_active"] = is_active

        return await self._count_all(
            tenant_id=tenant_id.value,
            filters=filters,
            search=None,
            search_fields=None,
        )
