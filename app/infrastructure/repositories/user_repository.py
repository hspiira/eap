"""
User Repository Implementation

SQLAlchemy implementation of UserRepository interface.
Uses TenantScopedRepositoryImpl base class to eliminate boilerplate.
"""

from collections.abc import Sequence
from typing import Any

from sqlalchemy import func, select, update

from app.domain.entities.user import UserEntity
from app.domain.enums import UserStatus
from app.domain.repositories.user_repository import UserRepository
from app.domain.value_objects.core import Email, TenantId, UserId
from app.infrastructure.mappers.user_mapper import UserMapper
from app.infrastructure.models.user_model import UserModel
from app.infrastructure.repositories.base import TenantScopedRepositoryImpl


class UserRepositoryImpl(TenantScopedRepositoryImpl[UserEntity, UserModel, UserId], UserRepository):
    """
    SQLAlchemy implementation of UserRepository.

    Inherits common CRUD operations from TenantScopedRepositoryImpl.
    Only implements domain-specific queries.
    """

    model_class = UserModel
    id_column = "id"

    def _to_entity(self, model: UserModel) -> UserEntity:
        """Convert model to entity."""
        return UserMapper.to_entity(model)

    def _to_model(self, entity: UserEntity) -> UserModel:
        """Convert entity to model."""
        return UserMapper.to_model(entity)

    def _get_id_value(self, entity_id: UserId) -> Any:
        """Extract raw ID value."""
        return entity_id.value

    # Domain-specific queries (not in base class)

    async def get_by_email(self, email: Email, tenant_id: TenantId) -> UserEntity | None:
        """Get user by email within tenant, excluding soft-deleted users."""
        stmt = select(UserModel).where(
            UserModel.email == email.value,
            UserModel.tenant_id == tenant_id.value,
            UserModel.deleted_at.is_(None),
        )
        result = await self.session.execute(stmt)
        model = result.scalar_one_or_none()
        if not model:
            return None
        return self._to_entity(model)

    async def list_all(
        self,
        tenant_id: TenantId,
        status: UserStatus | None = None,
        is_email_verified: bool | None = None,
        search: str | None = None,
        limit: int = 100,
        offset: int = 0,
        sort_by: str = "created_at",
        sort_desc: bool = True,
    ) -> Sequence[UserEntity]:
        """List users with filtering, searching, and pagination."""
        # Build filters dict for base class
        filters: dict[str, Any] = {}
        if status:
            filters["status"] = status

        # Use base class for common functionality
        entities = await self._query_all(
            tenant_id=tenant_id.value,
            limit=limit,
            offset=offset,
            sort_by=sort_by,
            sort_desc=sort_desc,
            filters=filters,
            search=search,
            search_fields=["email"],
        )

        # Apply email verification filter (special case)
        if is_email_verified is not None:
            entities = [
                e for e in entities
                if e.is_email_verified == is_email_verified
            ]

        return entities

    async def count(
        self,
        tenant_id: TenantId,
        status: UserStatus | None = None,
        is_email_verified: bool | None = None,
        search: str | None = None,
    ) -> int:
        """Count users matching filters."""
        # For accurate count with email verification filter, use direct query
        stmt = select(func.count(UserModel.id)).where(
            UserModel.tenant_id == tenant_id.value,
            UserModel.deleted_at.is_(None),
        )

        if status:
            stmt = stmt.where(UserModel.status == status)
        if is_email_verified is not None:
            if is_email_verified:
                stmt = stmt.where(UserModel.email_verified_at.isnot(None))
            else:
                stmt = stmt.where(UserModel.email_verified_at.is_(None))
        if search:
            stmt = stmt.where(UserModel.email.ilike(f"%{search}%"))

        result = await self.session.execute(stmt)
        return int(result.scalar() or 0)

    async def update_password(self, user_id: UserId, password_hash: str) -> bool:
        """Update a user's password hash."""
        stmt = (
            update(UserModel)
            .where(UserModel.id == user_id.value)
            .where(UserModel.deleted_at.is_(None))
            .values(password_hash=password_hash)
        )
        result = await self.session.execute(stmt)
        return result.rowcount > 0
