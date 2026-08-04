"""
Contract Repository Implementation

SQLAlchemy implementation of ContractRepository interface.
Uses TenantScopedRepositoryImpl base class to eliminate boilerplate.
"""

from collections.abc import Sequence
from datetime import datetime
from typing import Any

from sqlalchemy import select

from app.domain.entities.contract import ContractEntity
from app.domain.enums import ContractStatus, PaymentStatus
from app.domain.repositories.contract_repository import ContractRepository
from app.domain.value_objects.core import ClientId, ContractId, TenantId
from app.infrastructure.mappers.contract_mapper import ContractMapper
from app.infrastructure.models.contract_model import ContractModel
from app.infrastructure.repositories.base import TenantScopedRepositoryImpl


class ContractRepositoryImpl(
    TenantScopedRepositoryImpl[ContractEntity, ContractModel, ContractId], ContractRepository
):
    """
    SQLAlchemy implementation of ContractRepository.

    Inherits common CRUD operations from TenantScopedRepositoryImpl.
    Only implements domain-specific queries.
    """

    model_class = ContractModel
    id_column = "id"

    def _to_entity(self, model: ContractModel) -> ContractEntity:
        """Convert model to entity."""
        return ContractMapper.to_entity(model)

    def _to_model(self, entity: ContractEntity) -> ContractModel:
        """Convert entity to model."""
        return ContractMapper.to_model(entity)

    def _get_id_value(self, entity_id: ContractId) -> Any:
        """Extract raw ID value."""
        return entity_id.value

    async def get_by_client_id(
        self, tenant_id: TenantId, client_id: ClientId
    ) -> list[ContractEntity]:
        """Get all contracts for a client within tenant."""
        stmt = select(ContractModel).where(
            ContractModel.tenant_id == tenant_id.value,
            ContractModel.client_id == client_id.value,
            ContractModel.deleted_at.is_(None),
        )
        result = await self.session.execute(stmt)
        models = result.scalars().all()

        return [self._to_entity(model) for model in models]

    async def get_active_by_client_id(
        self, tenant_id: TenantId, client_id: ClientId
    ) -> ContractEntity | None:
        """Get active contract for a client within tenant."""
        stmt = select(ContractModel).where(
            ContractModel.tenant_id == tenant_id.value,
            ContractModel.client_id == client_id.value,
            ContractModel.status.in_([ContractStatus.ACTIVE, ContractStatus.RENEWED]),
            ContractModel.deleted_at.is_(None),
        )
        result = await self.session.execute(stmt)
        model = result.scalar_one_or_none()

        if not model:
            return None

        return self._to_entity(model)

    def _base_filters(
        self,
        client_id: ClientId | None,
        status: ContractStatus | None,
        payment_status: PaymentStatus | None,
        is_auto_renew: bool | None,
    ) -> dict[str, Any]:
        filters: dict[str, Any] = {}
        if client_id:
            filters["client_id"] = client_id.value
        if status:
            filters["status"] = status
        if payment_status:
            filters["payment_status"] = payment_status
        if is_auto_renew is not None:
            filters["is_auto_renew"] = is_auto_renew
        return filters

    @staticmethod
    def _ends_conditions(ends_from: datetime | None, ends_to: datetime | None) -> list[Any]:
        """
        Inclusive window on the end of the contract term.

        This is what the renewal window scans. It only became expressible once the
        term moved out of the `period` JSON blob into an indexed column.
        """
        conditions: list[Any] = []
        if ends_from is not None:
            conditions.append(ContractModel.end_date >= ends_from)
        if ends_to is not None:
            conditions.append(ContractModel.end_date <= ends_to)
        return conditions

    async def list_all(
        self,
        tenant_id: TenantId,
        client_id: ClientId | None = None,
        status: ContractStatus | None = None,
        payment_status: PaymentStatus | None = None,
        is_auto_renew: bool | None = None,
        ends_from: datetime | None = None,
        ends_to: datetime | None = None,
        search: str | None = None,
        limit: int = 100,
        offset: int = 0,
        sort_by: str = "created_at",
        sort_desc: bool = True,
    ) -> Sequence[ContractEntity]:
        """List contracts with filtering, searching, and pagination."""
        return await self._query_all(
            tenant_id=tenant_id.value,
            limit=limit,
            offset=offset,
            sort_by=sort_by,
            sort_desc=sort_desc,
            filters=self._base_filters(client_id, status, payment_status, is_auto_renew),
            search=None,
            search_fields=None,
            extra_conditions=self._ends_conditions(ends_from, ends_to),
        )

    async def count(
        self,
        tenant_id: TenantId,
        client_id: ClientId | None = None,
        status: ContractStatus | None = None,
        payment_status: PaymentStatus | None = None,
        is_auto_renew: bool | None = None,
        ends_from: datetime | None = None,
        ends_to: datetime | None = None,
        search: str | None = None,
    ) -> int:
        """Count contracts matching filters. Must mirror list_all exactly."""
        return await self._count_all(
            tenant_id=tenant_id.value,
            filters=self._base_filters(client_id, status, payment_status, is_auto_renew),
            extra_conditions=self._ends_conditions(ends_from, ends_to),
            search=None,
            search_fields=None,
        )
