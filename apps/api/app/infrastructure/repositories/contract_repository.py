"""
Contract Repository Implementation

SQLAlchemy implementation of ContractRepository interface.
Uses TenantScopedRepositoryImpl base class to eliminate boilerplate.
"""

from collections.abc import Sequence
from datetime import date
from typing import Any

from sqlalchemy import Date, and_, cast, func, select

from app.domain.entities.contract import ContractEntity
from app.domain.enums import ContractStatus, PaymentStatus, SessionStatus
from app.domain.repositories.contract_repository import ContractMetricsRow, ContractRepository
from app.domain.value_objects.core import ClientId, ContractId, TenantId
from app.infrastructure.mappers.contract_mapper import ContractMapper
from app.infrastructure.models.contract_model import ContractModel
from app.infrastructure.models.service_assignment_model import ServiceAssignmentModel
from app.infrastructure.models.service_session_model import ServiceSessionModel
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

    async def find_overlapping(
        self,
        tenant_id: TenantId,
        client_id: ClientId,
        *,
        start_date: date,
        end_date: date,
        exclude_id: ContractId | None = None,
    ) -> list[ContractEntity]:
        """Terms for this client whose period intersects the given one."""
        stmt = select(ContractModel).where(
            ContractModel.tenant_id == tenant_id.value,
            ContractModel.client_id == client_id.value,
            ContractModel.deleted_at.is_(None),
            ContractModel.status != ContractStatus.TERMINATED,
            ContractModel.start_date <= end_date,
            ContractModel.end_date >= start_date,
        )
        if exclude_id is not None:
            stmt = stmt.where(ContractModel.id != exclude_id.value)
        result = await self.session.execute(stmt)
        return [self._to_entity(model) for model in result.scalars().all()]

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
    def _ends_conditions(ends_from: date | None, ends_to: date | None) -> list[Any]:
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
        ends_from: date | None = None,
        ends_to: date | None = None,
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
        ends_from: date | None = None,
        ends_to: date | None = None,
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

    async def get_metrics_for_client(
        self, tenant_id: TenantId, client_id: ClientId
    ) -> list[ContractMetricsRow]:
        """Count each contract's covered services and sum its completed sessions' cost.

        The date is taken in UTC before truncating, as `date_trunc` on a
        timestamptz otherwise buckets by the connection's timezone.
        """
        session_day = cast(func.timezone("UTC", ServiceSessionModel.scheduled_at), Date)
        services = (
            select(func.count(ServiceAssignmentModel.id))
            .where(
                ServiceAssignmentModel.contract_id == ContractModel.id,
                ServiceAssignmentModel.deleted_at.is_(None),
            )
            .correlate(ContractModel)
            .scalar_subquery()
        )
        rows = await self.session.execute(
            select(
                ContractModel.id,
                services,
                func.count(ServiceSessionModel.id),
                func.count(ServiceSessionModel.rate_ugx),
                func.coalesce(func.sum(ServiceSessionModel.rate_ugx), 0),
            )
            .select_from(ContractModel)
            .outerjoin(
                ServiceSessionModel,
                and_(
                    ServiceSessionModel.tenant_id == ContractModel.tenant_id,
                    ServiceSessionModel.client_id == ContractModel.client_id,
                    ServiceSessionModel.deleted_at.is_(None),
                    ServiceSessionModel.status == SessionStatus.COMPLETED,
                    session_day.between(ContractModel.start_date, ContractModel.end_date),
                ),
            )
            .where(
                ContractModel.tenant_id == tenant_id.value,
                ContractModel.client_id == client_id.value,
                ContractModel.deleted_at.is_(None),
            )
            .group_by(ContractModel.id)
        )
        return [
            ContractMetricsRow(
                contract_id=contract_id,
                services=int(services_count),
                sessions=int(sessions),
                sessions_priced=int(priced),
                spent=int(total),
            )
            for contract_id, services_count, sessions, priced, total in rows
        ]
