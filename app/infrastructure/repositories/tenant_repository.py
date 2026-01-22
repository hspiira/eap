"""
Tenant Repository Implementation

SQLAlchemy implementation of TenantRepository interface.
"""

from typing import Sequence

from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.entities.tenant import TenantEntity
from app.domain.enums import SubscriptionTier, TenantStatus
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
    
    def __init__(self, session: AsyncSession) -> None:
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
        stmt = select(TenantModel).where(
            TenantModel.id == tenant_id.value,
            TenantModel.deleted_at.is_(None),
        )
        result = await self.session.execute(stmt)
        model = result.scalar_one_or_none()
        
        if model:
            from app.shared.utils.datetime import utc_now
            now = utc_now()
            model.deleted_at = now
            model.updated_at = now
            await self.session.merge(model)
    
    async def exists(self, tenant_id: TenantId) -> bool:
        """Check if tenant exists (not soft-deleted)."""
        from sqlalchemy import exists as sql_exists
        stmt = sql_exists().where(
            TenantModel.id == tenant_id.value,
            TenantModel.deleted_at.is_(None)
        ).select()
        result = await self.session.execute(stmt)
        return bool(result.scalar())
    
    async def list_all(
        self,
        status: TenantStatus | None = None,
        subscription_tier: SubscriptionTier | None = None,
        search: str | None = None,
        limit: int = 100,
        offset: int = 0,
        sort_by: str = "created_at",
        sort_desc: bool = True,
    ) -> Sequence[TenantEntity]:
        """List tenants with filtering, searching, and pagination."""
        stmt = select(TenantModel).where(
            TenantModel.deleted_at.is_(None)
        )
        
        # Apply filters
        if status:
            stmt = stmt.where(TenantModel.status == status)
        if subscription_tier:
            stmt = stmt.where(TenantModel.subscription_tier == subscription_tier)
        if search:
            search_pattern = f"%{search.lower()}%"
            stmt = stmt.where(
                or_(
                    TenantModel.name.ilike(search_pattern),
                    TenantModel.code.ilike(search_pattern),
                )
            )
        
        # Apply sorting
        sort_column = getattr(TenantModel, sort_by, TenantModel.created_at)
        if sort_desc:
            stmt = stmt.order_by(sort_column.desc())
        else:
            stmt = stmt.order_by(sort_column.asc())
        
        # Apply pagination
        stmt = stmt.limit(limit).offset(offset)
        
        result = await self.session.execute(stmt)
        models = result.scalars().all()
        
        return [TenantMapper.to_entity(model) for model in models]
    
    async def count(
        self,
        status: TenantStatus | None = None,
        subscription_tier: SubscriptionTier | None = None,
        search: str | None = None,
    ) -> int:
        """Count tenants matching filters."""
        stmt = select(func.count(TenantModel.id)).where(
            TenantModel.deleted_at.is_(None)
        )
        
        # Apply filters
        if status:
            stmt = stmt.where(TenantModel.status == status)
        if subscription_tier:
            stmt = stmt.where(TenantModel.subscription_tier == subscription_tier)
        if search:
            search_pattern = f"%{search.lower()}%"
            stmt = stmt.where(
                or_(
                    TenantModel.name.ilike(search_pattern),
                    TenantModel.code.ilike(search_pattern),
                )
            )
        
        result = await self.session.execute(stmt)
        return int(result.scalar() or 0)
