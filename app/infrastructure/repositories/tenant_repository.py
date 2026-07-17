"""
Tenant Repository Implementation

SQLAlchemy implementation of TenantRepository interface.
Uses BaseRepositoryImpl base class to eliminate boilerplate.

Note: Tenant is a root aggregate, so it uses BaseRepositoryImpl instead of
TenantScopedRepositoryImpl (tenants don't have a tenant_id on themselves).
"""

from collections.abc import Sequence
from typing import Any

from sqlalchemy import func, or_, select

from app.domain.entities.tenant import TenantEntity
from app.domain.enums import SubscriptionTier, TenantStatus
from app.domain.repositories.tenant_repository import TenantRepository
from app.domain.value_objects.core import TenantId
from app.infrastructure.mappers.tenant_mapper import TenantMapper
from app.infrastructure.models.tenant_model import TenantModel
from app.infrastructure.repositories.base import BaseRepositoryImpl


class TenantRepositoryImpl(BaseRepositoryImpl[TenantEntity, TenantModel, TenantId], TenantRepository):
    """
    SQLAlchemy implementation of TenantRepository.

    Inherits common CRUD operations from BaseRepositoryImpl.
    Only implements domain-specific queries.
    """

    model_class = TenantModel
    id_column = "id"

    def _to_entity(self, model: TenantModel) -> TenantEntity:
        """Convert model to entity."""
        return TenantMapper.to_entity(model)

    def _to_model(self, entity: TenantEntity) -> TenantModel:
        """Convert entity to model."""
        return TenantMapper.to_model(entity)

    def _get_id_value(self, entity_id: TenantId) -> Any:
        """Extract raw ID value."""
        return entity_id.value

    # Domain-specific queries (not in base class)

    async def get_by_azure_tenant_id(self, azure_tenant_id: str) -> TenantEntity | None:
        """Get tenant by Azure AD directory ID, excluding soft-deleted tenants."""
        stmt = select(TenantModel).where(
            TenantModel.azure_tenant_id == azure_tenant_id,
            TenantModel.deleted_at.is_(None),
        )
        result = await self.session.execute(stmt)
        model = result.scalar_one_or_none()
        if not model:
            return None
        return self._to_entity(model)

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

        return self._to_entity(model)

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

        ALLOWED_SORT_COLUMNS = {"created_at", "updated_at", "name", "code", "status"}
        if sort_by not in ALLOWED_SORT_COLUMNS:
            raise ValueError(f"Invalid sort_by value: {sort_by}. Allowed values: {ALLOWED_SORT_COLUMNS}")
        if sort_desc:
            stmt = stmt.order_by(getattr(TenantModel, sort_by).desc())
        else:
            stmt = stmt.order_by(getattr(TenantModel, sort_by).asc())

        # Apply pagination
        stmt = stmt.limit(limit).offset(offset)

        result = await self.session.execute(stmt)
        models = result.scalars().all()

        return [self._to_entity(model) for model in models]

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
