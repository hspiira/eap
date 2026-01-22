"""
Contract Repository Implementation

SQLAlchemy implementation of ContractRepository interface.
"""

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.entities.contract import ContractEntity
from app.domain.enums import ContractStatus
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
        stmt = select(ContractModel).where(ContractModel.id == contract_id.value)
        result = await self.session.execute(stmt)
        model = result.scalar_one_or_none()

        if model:
            from app.shared.utils.datetime import utc_now

            model.deleted_at = utc_now()
            await self.session.merge(model)

    async def exists(self, contract_id: ContractId) -> bool:
        """Check if contract exists (not soft-deleted)."""
        stmt = select(ContractModel).where(
            ContractModel.id == contract_id.value,
            ContractModel.deleted_at.is_(None),
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none() is not None
