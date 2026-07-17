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

    async def get_by_azure_oid(self, azure_oid: str, tenant_id: TenantId) -> UserEntity | None:
        """Get user by Azure Object ID within tenant, excluding soft-deleted users."""
        stmt = select(UserModel).where(
            UserModel.azure_oid == azure_oid,
            UserModel.tenant_id == tenant_id.value,
            UserModel.deleted_at.is_(None),
        )
        result = await self.session.execute(stmt)
        model = result.scalar_one_or_none()
        if not model:
            return None
        return self._to_entity(model)

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
        is_two_factor_enabled: bool | None = None,
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
        if is_two_factor_enabled is not None:
            filters["is_two_factor_enabled"] = is_two_factor_enabled

        # Verification is stored as a nullable timestamp, so it cannot go through
        # the equality-based `filters` dict. It must still be applied in SQL: this
        # filter used to run in Python over the already-paginated page, which
        # returned fewer rows than `limit` and disagreed with `count()` below.
        return await self._query_all(
            tenant_id=tenant_id.value,
            limit=limit,
            offset=offset,
            sort_by=sort_by,
            sort_desc=sort_desc,
            filters=filters,
            search=search,
            search_fields=["email"],
            extra_conditions=self._verified_conditions(is_email_verified),
        )

    @staticmethod
    def _verified_conditions(is_email_verified: bool | None) -> list[Any]:
        """SQL conditions for the `is_email_verified` flag. Shared by list_all/count."""
        if is_email_verified is None:
            return []
        if is_email_verified:
            return [UserModel.email_verified_at.isnot(None)]
        return [UserModel.email_verified_at.is_(None)]

    async def count(
        self,
        tenant_id: TenantId,
        status: UserStatus | None = None,
        is_email_verified: bool | None = None,
        is_two_factor_enabled: bool | None = None,
        search: str | None = None,
    ) -> int:
        """Count users matching filters. Must mirror list_all's filters exactly."""
        stmt = select(func.count(UserModel.id)).where(
            UserModel.tenant_id == tenant_id.value,
            UserModel.deleted_at.is_(None),
        )

        if status:
            stmt = stmt.where(UserModel.status == status)
        if is_two_factor_enabled is not None:
            stmt = stmt.where(UserModel.is_two_factor_enabled == is_two_factor_enabled)
        for condition in self._verified_conditions(is_email_verified):
            stmt = stmt.where(condition)
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
