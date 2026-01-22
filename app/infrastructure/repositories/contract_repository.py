"""
Contract Repository Implementation

SQLAlchemy implementation of ContractRepository interface.
"""

from typing import Sequence

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.entities.contract import ContractEntity
from app.domain.enums import ContractStatus, PaymentStatus
from app.domain.repositories.contract_repository import ContractRepository
from app.domain.value_objects.core import ClientId, ContractId, TenantId
from app.infrastructure.mappers.contract_mapper import ContractMapper
from app.infrastructure.models.contract_model import ContractModel


class ContractRepositoryImpl(ContractRepository):
    """
    SQLAlchemy implementation of ContractRepository.

    Handles data access for Contract aggregate.
    Uses mapper to convert between entity and model.
    """

    def __init__(self, session: AsyncSession) -> None:
        """
        Initialize repository with database session.

        Args:
            session: SQLAlchemy async database session
        """
        self.session = session

    async def get_by_id(self, contract_id: ContractId) -> ContractEntity | None:
        """Get contract by ID, excluding soft-deleted contracts."""
        stmt = select(ContractModel).where(
            ContractModel.id == contract_id.value,
            ContractModel.deleted_at.is_(None),
        )
        result = await self.session.execute(stmt)
        model = result.scalar_one_or_none()

        if not model:
            return None

        return ContractMapper.to_entity(model)

    async def get_by_client_id(
        self, tenant_id: TenantId, client_id: ClientId
    ) -> list[ContractEntity]:
        """Get all contracts for a client within tenant, excluding soft-deleted."""
        stmt = select(ContractModel).where(
            ContractModel.tenant_id == tenant_id.value,
            ContractModel.client_id == client_id.value,
            ContractModel.deleted_at.is_(None),
        )
        result = await self.session.execute(stmt)
        models = result.scalars().all()

        return [ContractMapper.to_entity(model) for model in models]

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

        return ContractMapper.to_entity(model)

    async def save(self, contract: ContractEntity) -> None:
        """
        Save contract aggregate atomically.

        Uses merge to handle both insert and update.
        """
        model = ContractMapper.to_model(contract)
        await self.session.merge(model)
        # Note: commit is typically handled by the application service/unit of work

    async def delete(self, contract_id: ContractId) -> None:
        """
        Soft delete contract.

        In practice, this is usually done by calling contract.terminate()
        and then save(), but this method provides explicit soft delete.
        """
        stmt = select(ContractModel).where(
            ContractModel.id == contract_id.value,
            ContractModel.deleted_at.is_(None),
        )
        result = await self.session.execute(stmt)
        model = result.scalar_one_or_none()

        if model:
            from app.shared.utils.datetime import utc_now

            now = utc_now()
            model.deleted_at = now
            model.updated_at = now
            await self.session.merge(model)

    async def exists(self, contract_id: ContractId) -> bool:
        """Check if contract exists (not soft-deleted)."""
        from sqlalchemy import exists as sql_exists
        stmt = sql_exists().where(
            ContractModel.id == contract_id.value,
            ContractModel.deleted_at.is_(None),
        ).select()
        result = await self.session.execute(stmt)
        return bool(result.scalar())
    
    async def list_all(
        self,
        tenant_id: TenantId,
        client_id: ClientId | None = None,
        status: ContractStatus | None = None,
        payment_status: PaymentStatus | None = None,
        search: str | None = None,
        limit: int = 100,
        offset: int = 0,
        sort_by: str = "created_at",
        sort_desc: bool = True,
    ) -> Sequence[ContractEntity]:
        """List contracts with filtering, searching, and pagination."""
        stmt = select(ContractModel).where(
            ContractModel.tenant_id == tenant_id.value,
            ContractModel.deleted_at.is_(None),
        )
        
        # Apply filters
        if client_id:
            stmt = stmt.where(ContractModel.client_id == client_id.value)
        if status:
            stmt = stmt.where(ContractModel.status == status)
        if payment_status:
            stmt = stmt.where(ContractModel.payment_status == payment_status)
        # Note: search not implemented as contracts don't have searchable text fields
        
        # Apply sorting
        sort_column = getattr(ContractModel, sort_by, ContractModel.created_at)
        if sort_desc:
            stmt = stmt.order_by(sort_column.desc())
        else:
            stmt = stmt.order_by(sort_column.asc())
        
        # Apply pagination
        stmt = stmt.limit(limit).offset(offset)
        
        result = await self.session.execute(stmt)
        models = result.scalars().all()
        
        return [ContractMapper.to_entity(model) for model in models]
    
    async def count(
        self,
        tenant_id: TenantId,
        client_id: ClientId | None = None,
        status: ContractStatus | None = None,
        payment_status: PaymentStatus | None = None,
        search: str | None = None,
    ) -> int:
        """Count contracts matching filters."""
        stmt = select(func.count(ContractModel.id)).where(
            ContractModel.tenant_id == tenant_id.value,
            ContractModel.deleted_at.is_(None),
        )
        
        # Apply filters
        if client_id:
            stmt = stmt.where(ContractModel.client_id == client_id.value)
        if status:
            stmt = stmt.where(ContractModel.status == status)
        if payment_status:
            stmt = stmt.where(ContractModel.payment_status == payment_status)
        
        result = await self.session.execute(stmt)
        return int(result.scalar() or 0)
