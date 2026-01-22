"""
Tenant Repository Implementation

SQLAlchemy implementation of TenantRepository interface.
"""

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.entities.tenant import TenantEntity
from app.domain.repositories.tenant_repository import TenantRepository
from app.domain.value_objects.core import TenantId
from app.infrastructure.mappers.tenant_mapper import TenantMapper
from app.infrastructure.models.tenant_model import TenantModel


class TenantRepositoryImpl(TenantRepository):
    """
    SQLAlchemy implementation of TenantRepository.
    
    Handles data access for Tenant aggregate.
    Uses mapper to convert between entity and model.
    """
    
    def __init__(self, session: AsyncSession):
        """
        Initialize repository with database session.
        
        Args:
            session: SQLAlchemy async database session
        """
        self.session = session
    
    async def get_by_id(self, tenant_id: TenantId) -> TenantEntity | None:
        """Get tenant by ID, excluding soft-deleted tenants."""
        stmt = select(TenantModel).where(
            TenantModel.id == tenant_id.value,
            TenantModel.deleted_at.is_(None)
        )
        result = await self.session.execute(stmt)
        model = result.scalar_one_or_none()
        
        if not model:
            return None
        
        return TenantMapper.to_entity(model)
    
    async def get_by_code(self, code: str) -> TenantEntity | None:
        """Get tenant by code, excluding soft-deleted tenants."""
        stmt = select(TenantModel).where(
            TenantModel.code == code,
            TenantModel.deleted_at.is_(None)
        )
        result = await self.session.execute(stmt)
        model = result.scalar_one_or_none()
        
        if not model:
            return None
        
        return TenantMapper.to_entity(model)
    
    async def save(self, tenant: TenantEntity) -> None:
        """
        Save tenant aggregate atomically.
        
        Uses merge to handle both insert and update.
        """
        model = TenantMapper.to_model(tenant)
        await self.session.merge(model)
        # Note: commit is typically handled by the application service/unit of work
    
    async def delete(self, tenant_id: TenantId) -> None:
        """
        Soft delete tenant.
        
        In practice, this is usually done by calling tenant.terminate()
        and then save(), but this method provides explicit soft delete.
        """
        stmt = select(TenantModel).where(TenantModel.id == tenant_id.value)
        result = await self.session.execute(stmt)
        model = result.scalar_one_or_none()
        
        if model:
            from app.shared.utils.datetime import utc_now
            model.deleted_at = utc_now()
            await self.session.merge(model)
    
    async def exists(self, tenant_id: TenantId) -> bool:
        """Check if tenant exists (not soft-deleted)."""
        stmt = select(TenantModel).where(
            TenantModel.id == tenant_id.value,
            TenantModel.deleted_at.is_(None)
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none() is not None
