"""
User Repository Implementation

SQLAlchemy implementation of UserRepository interface.
"""

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.entities.user import UserEntity
from app.domain.repositories.user_repository import UserRepository
from app.domain.value_objects.core import Email, TenantId, UserId
from app.infrastructure.mappers.user_mapper import UserMapper
from app.infrastructure.models.user_model import UserModel
from app.shared.utils.datetime import utc_now


class UserRepositoryImpl(UserRepository):
    """
    SQLAlchemy implementation of UserRepository.

    Handles data access for User aggregate.
    Uses mapper to convert between entity and model.
    """

    def __init__(self, session: AsyncSession) -> None:
        """
        Initialize repository with database session.

        Args:
            session: SQLAlchemy async database session
        """
        self.session = session

    async def get_by_id(self, user_id: UserId) -> UserEntity | None:
        """Get user by ID, excluding soft-deleted users."""
        stmt = select(UserModel).where(
            UserModel.id == user_id.value,
            UserModel.deleted_at.is_(None),
        )
        result = await self.session.execute(stmt)
        model = result.scalar_one_or_none()

        if not model:
            return None
        return UserMapper.to_entity(model)

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
        return UserMapper.to_entity(model)

    async def save(self, user: UserEntity) -> None:
        """
        Save user aggregate atomically.

        Uses merge to handle both insert and update.
        """
        model = UserMapper.to_model(user)
        await self.session.merge(model)
        # Note: commit is typically handled by the application service/unit of work

    async def delete(self, user_id: UserId) -> None:
        """
        Soft delete user.

        In practice, this is usually done by calling user.ban() or similar
        and then save(), but this method provides explicit soft delete.
        """
        stmt = select(UserModel).where(
            UserModel.id == user_id.value,
            UserModel.deleted_at.is_(None),
        )
        result = await self.session.execute(stmt)
        model = result.scalar_one_or_none()

        if model:
            now = utc_now()
            model.deleted_at = now
            model.updated_at = now
            await self.session.merge(model)

    async def exists(self, user_id: UserId) -> bool:
        """Check if user exists (not soft-deleted)."""
        from sqlalchemy import exists as sql_exists
        stmt = sql_exists().where(
            UserModel.id == user_id.value,
            UserModel.deleted_at.is_(None),
        ).select()
        result = await self.session.execute(stmt)
        return bool(result.scalar())
