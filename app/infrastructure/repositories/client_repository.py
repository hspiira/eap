"""
Client Repository Implementation

SQLAlchemy implementation of ClientRepository interface.
"""

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.entities.client import ClientEntity
from app.domain.repositories.client_repository import ClientRepository
from app.domain.value_objects.core import ClientId, TenantId
from app.infrastructure.mappers.client_mapper import ClientMapper
from app.infrastructure.models.client_model import ClientModel
from app.shared.utils.datetime import utc_now


class ClientRepositoryImpl(ClientRepository):
    """
    SQLAlchemy implementation of ClientRepository.

    Handles data access for Client aggregate.
    Uses mapper to convert between entity and model.
    """

    def __init__(self, session: AsyncSession) -> None:
        """
        Initialize repository with database session.

        Args:
            session: SQLAlchemy async database session
        """
        self.session = session

    async def get_by_id(self, client_id: ClientId) -> ClientEntity | None:
        """Get client by ID, excluding soft-deleted clients."""
        stmt = select(ClientModel).where(
            ClientModel.id == client_id.value,
            ClientModel.deleted_at.is_(None),
        )
        result = await self.session.execute(stmt)
        model = result.scalar_one_or_none()

        if not model:
            return None

        return ClientMapper.to_entity(model)

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

        return ClientMapper.to_entity(model)

    async def save(self, client: ClientEntity) -> None:
        """
        Save client aggregate atomically.

        Uses merge to handle both insert and update.
        """
        model = ClientMapper.to_model(client)
        await self.session.merge(model)
        # Note: commit is typically handled by the application service/unit of work

    async def delete(self, client_id: ClientId) -> None:
        """
        Soft delete client.

        In practice, this is usually done by calling client methods
        and then save(), but this method provides explicit soft delete.
        """
        stmt = select(ClientModel).where(
            ClientModel.id == client_id.value,
            ClientModel.deleted_at.is_(None),
        )
        result = await self.session.execute(stmt)
        model = result.scalar_one_or_none()

        if model:
            now = utc_now()
            model.deleted_at = now
            model.updated_at = now
            await self.session.merge(model)

    async def exists(self, client_id: ClientId) -> bool:
        """Check if client exists (not soft-deleted)."""
        stmt = select(ClientModel.id).where(
            ClientModel.id == client_id.value,
            ClientModel.deleted_at.is_(None),
        )
        result = await self.session.execute(stmt)
        return bool(result.scalar())
