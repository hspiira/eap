"""ServiceAssignment Repository Implementation - SQLAlchemy implementation."""

from typing import Sequence

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.entities.service_assignment import ServiceAssignmentEntity
from app.domain.enums import BaseStatus
from app.domain.repositories.service_assignment_repository import ServiceAssignmentRepository
from app.domain.value_objects.core import ContractId, ServiceAssignmentId, ServiceId, TenantId
from app.infrastructure.mappers.service_assignment_mapper import ServiceAssignmentMapper
from app.infrastructure.models.service_assignment_model import ServiceAssignmentModel
from app.shared.utils.datetime import utc_now


class ServiceAssignmentRepositoryImpl(ServiceAssignmentRepository):
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def get_by_id(self, assignment_id: ServiceAssignmentId) -> ServiceAssignmentEntity | None:
        stmt = select(ServiceAssignmentModel).where(
            ServiceAssignmentModel.id == assignment_id.value,
            ServiceAssignmentModel.deleted_at.is_(None),
        )
        result = await self.session.execute(stmt)
        model = result.scalar_one_or_none()
        return ServiceAssignmentMapper.to_entity(model) if model else None

    async def get_by_service_id(self, service_id: ServiceId, tenant_id: TenantId) -> Sequence[ServiceAssignmentEntity]:
        stmt = select(ServiceAssignmentModel).where(
            ServiceAssignmentModel.service_id == service_id.value,
            ServiceAssignmentModel.tenant_id == tenant_id.value,
            ServiceAssignmentModel.deleted_at.is_(None),
        )
        result = await self.session.execute(stmt)
        models = result.scalars().all()
        return [ServiceAssignmentMapper.to_entity(m) for m in models]

    async def get_by_contract_id(self, contract_id: ContractId, tenant_id: TenantId) -> Sequence[ServiceAssignmentEntity]:
        stmt = select(ServiceAssignmentModel).where(
            ServiceAssignmentModel.contract_id == contract_id.value,
            ServiceAssignmentModel.tenant_id == tenant_id.value,
            ServiceAssignmentModel.deleted_at.is_(None),
        )
        result = await self.session.execute(stmt)
        models = result.scalars().all()
        return [ServiceAssignmentMapper.to_entity(m) for m in models]

    async def get_by_service_and_contract(
        self, service_id: ServiceId, contract_id: ContractId, tenant_id: TenantId
    ) -> ServiceAssignmentEntity | None:
        stmt = select(ServiceAssignmentModel).where(
            ServiceAssignmentModel.service_id == service_id.value,
            ServiceAssignmentModel.contract_id == contract_id.value,
            ServiceAssignmentModel.tenant_id == tenant_id.value,
            ServiceAssignmentModel.deleted_at.is_(None),
        )
        result = await self.session.execute(stmt)
        model = result.scalar_one_or_none()
        return ServiceAssignmentMapper.to_entity(model) if model else None

    async def list_all(
        self,
        tenant_id: TenantId,
        service_id: ServiceId | None = None,
        contract_id: ContractId | None = None,
        status: BaseStatus | None = None,
        limit: int = 100,
        offset: int = 0,
    ) -> Sequence[ServiceAssignmentEntity]:
        stmt = select(ServiceAssignmentModel).where(
            ServiceAssignmentModel.tenant_id == tenant_id.value,
            ServiceAssignmentModel.deleted_at.is_(None),
        )
        if service_id:
            stmt = stmt.where(ServiceAssignmentModel.service_id == service_id.value)
        if contract_id:
            stmt = stmt.where(ServiceAssignmentModel.contract_id == contract_id.value)
        if status:
            stmt = stmt.where(ServiceAssignmentModel.status == status)
        stmt = stmt.order_by(ServiceAssignmentModel.created_at.desc()).limit(limit).offset(offset)
        result = await self.session.execute(stmt)
        return [ServiceAssignmentMapper.to_entity(m) for m in result.scalars().all()]

    async def count(
        self,
        tenant_id: TenantId,
        service_id: ServiceId | None = None,
        contract_id: ContractId | None = None,
        status: BaseStatus | None = None,
    ) -> int:
        stmt = select(func.count(ServiceAssignmentModel.id)).where(
            ServiceAssignmentModel.tenant_id == tenant_id.value,
            ServiceAssignmentModel.deleted_at.is_(None),
        )
        if service_id:
            stmt = stmt.where(ServiceAssignmentModel.service_id == service_id.value)
        if contract_id:
            stmt = stmt.where(ServiceAssignmentModel.contract_id == contract_id.value)
        if status:
            stmt = stmt.where(ServiceAssignmentModel.status == status)
        result = await self.session.execute(stmt)
        return int(result.scalar() or 0)

    async def save(self, assignment: ServiceAssignmentEntity) -> None:
        model = ServiceAssignmentMapper.to_model(assignment)
        await self.session.merge(model)

    async def delete(self, assignment_id: ServiceAssignmentId) -> None:
        stmt = select(ServiceAssignmentModel).where(
            ServiceAssignmentModel.id == assignment_id.value,
            ServiceAssignmentModel.deleted_at.is_(None),
        )
        result = await self.session.execute(stmt)
        model = result.scalar_one_or_none()
        if model:
            model.deleted_at = utc_now()
            model.updated_at = utc_now()
            await self.session.merge(model)

    async def exists(self, assignment_id: ServiceAssignmentId) -> bool:
        from sqlalchemy import exists as sql_exists
        stmt = sql_exists().where(
            ServiceAssignmentModel.id == assignment_id.value,
            ServiceAssignmentModel.deleted_at.is_(None),
        ).select()
        result = await self.session.execute(stmt)
        return bool(result.scalar())
