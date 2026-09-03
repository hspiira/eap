"""ServiceAssignment Repository Implementation - SQLAlchemy implementation."""

from collections.abc import Sequence
from typing import Any

from sqlalchemy import select

from app.domain.entities.service_assignment import ServiceAssignmentEntity
from app.domain.enums import BaseStatus
from app.domain.repositories.service_assignment_repository import ServiceAssignmentRepository
from app.domain.value_objects.core import ContractId, ServiceAssignmentId, ServiceId, TenantId
from app.infrastructure.mappers.service_assignment_mapper import ServiceAssignmentMapper
from app.infrastructure.models.service_assignment_model import ServiceAssignmentModel
from app.infrastructure.repositories.base import TenantScopedRepositoryImpl


class ServiceAssignmentRepositoryImpl(
    TenantScopedRepositoryImpl[
        ServiceAssignmentEntity, ServiceAssignmentModel, ServiceAssignmentId
    ],
    ServiceAssignmentRepository,
):
    """
    SQLAlchemy implementation of ServiceAssignmentRepository.

    Inherits common CRUD operations from TenantScopedRepositoryImpl.
    Only implements domain-specific queries.
    """

    model_class = ServiceAssignmentModel
    id_column = "id"

    def _to_entity(self, model: ServiceAssignmentModel) -> ServiceAssignmentEntity:
        """Convert model to entity."""
        return ServiceAssignmentMapper.to_entity(model)

    def _to_model(self, entity: ServiceAssignmentEntity) -> ServiceAssignmentModel:
        """Convert entity to model."""
        return ServiceAssignmentMapper.to_model(entity)

    def _get_id_value(self, entity_id: ServiceAssignmentId) -> Any:
        """Extract raw ID value."""
        return entity_id.value

    # Domain-specific queries (not in base class)

    async def get_by_service_id(
        self, service_id: ServiceId, tenant_id: TenantId
    ) -> Sequence[ServiceAssignmentEntity]:
        """Get all assignments for a service."""
        stmt = select(ServiceAssignmentModel).where(
            ServiceAssignmentModel.service_id == service_id.value,
            ServiceAssignmentModel.tenant_id == tenant_id.value,
            ServiceAssignmentModel.deleted_at.is_(None),
        )
        result = await self.session.execute(stmt)
        models = result.scalars().all()
        return [self._to_entity(m) for m in models]

    async def get_by_contract_id(
        self, contract_id: ContractId, tenant_id: TenantId
    ) -> Sequence[ServiceAssignmentEntity]:
        """Get all assignments for a contract."""
        stmt = select(ServiceAssignmentModel).where(
            ServiceAssignmentModel.contract_id == contract_id.value,
            ServiceAssignmentModel.tenant_id == tenant_id.value,
            ServiceAssignmentModel.deleted_at.is_(None),
        )
        result = await self.session.execute(stmt)
        models = result.scalars().all()
        return [self._to_entity(m) for m in models]

    async def get_by_service_and_contract(
        self, service_id: ServiceId, contract_id: ContractId, tenant_id: TenantId
    ) -> ServiceAssignmentEntity | None:
        """Get assignment by service and contract."""
        stmt = select(ServiceAssignmentModel).where(
            ServiceAssignmentModel.service_id == service_id.value,
            ServiceAssignmentModel.contract_id == contract_id.value,
            ServiceAssignmentModel.tenant_id == tenant_id.value,
            ServiceAssignmentModel.deleted_at.is_(None),
        )
        result = await self.session.execute(stmt)
        model = result.scalar_one_or_none()
        return self._to_entity(model) if model else None

    async def list_all(
        self,
        tenant_id: TenantId,
        service_id: ServiceId | None = None,
        contract_id: ContractId | None = None,
        status: BaseStatus | None = None,
        limit: int = 100,
        offset: int = 0,
    ) -> Sequence[ServiceAssignmentEntity]:
        """List assignments with filtering and pagination."""
        # Build filters dict for base class
        filters: dict[str, Any] = {}
        if service_id:
            filters["service_id"] = service_id.value
        if contract_id:
            filters["contract_id"] = contract_id.value
        if status:
            filters["status"] = status

        return await self._query_all(
            tenant_id=tenant_id.value,
            limit=limit,
            offset=offset,
            sort_by="created_at",
            sort_desc=True,
            filters=filters,
            search=None,
            search_fields=None,
        )

    async def count(
        self,
        tenant_id: TenantId,
        service_id: ServiceId | None = None,
        contract_id: ContractId | None = None,
        status: BaseStatus | None = None,
    ) -> int:
        """Count assignments matching filters."""
        filters: dict[str, Any] = {}
        if service_id:
            filters["service_id"] = service_id.value
        if contract_id:
            filters["contract_id"] = contract_id.value
        if status:
            filters["status"] = status

        return await self._count_all(
            tenant_id=tenant_id.value,
            filters=filters,
            search=None,
            search_fields=None,
        )
