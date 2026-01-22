"""
Client Repository Implementation

SQLAlchemy implementation of ClientRepository interface.
"""

from typing import Sequence

from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.entities.client import ClientEntity
from app.domain.enums import BaseStatus
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
    
    async def list_all(
        self,
        tenant_id: TenantId,
        status: BaseStatus | None = None,
        is_verified: bool | None = None,
        search: str | None = None,
        limit: int = 100,
        offset: int = 0,
        sort_by: str = "created_at",
        sort_desc: bool = True,
    ) -> Sequence[ClientEntity]:
        """List clients with filtering, searching, and pagination."""
        stmt = select(ClientModel).where(
            ClientModel.tenant_id == tenant_id.value,
            ClientModel.deleted_at.is_(None),
        )
        
        # Apply filters
        if status:
            stmt = stmt.where(ClientModel.status == status)
        if is_verified is not None:
            stmt = stmt.where(ClientModel.is_verified == is_verified)
        if search:
            search_pattern = f"%{search.lower()}%"
            stmt = stmt.where(ClientModel.name.ilike(search_pattern))
        
        # Apply sorting
        sort_column = getattr(ClientModel, sort_by, ClientModel.created_at)
        if sort_desc:
            stmt = stmt.order_by(sort_column.desc())
        else:
            stmt = stmt.order_by(sort_column.asc())
        
        # Apply pagination
        stmt = stmt.limit(limit).offset(offset)
        
        result = await self.session.execute(stmt)
        models = result.scalars().all()
        
        return [ClientMapper.to_entity(model) for model in models]
    
    async def count(
        self,
        tenant_id: TenantId,
        status: BaseStatus | None = None,
        is_verified: bool | None = None,
        search: str | None = None,
    ) -> int:
        """Count clients matching filters."""
        stmt = select(func.count(ClientModel.id)).where(
            ClientModel.tenant_id == tenant_id.value,
            ClientModel.deleted_at.is_(None),
        )
        
        # Apply filters
        if status:
            stmt = stmt.where(ClientModel.status == status)
        if is_verified is not None:
            stmt = stmt.where(ClientModel.is_verified == is_verified)
        if search:
            search_pattern = f"%{search.lower()}%"
            stmt = stmt.where(ClientModel.name.ilike(search_pattern))
        
        result = await self.session.execute(stmt)
        return int(result.scalar() or 0)
