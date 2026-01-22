"""
User Repository Implementation

SQLAlchemy implementation of UserRepository interface.
"""

from typing import Sequence

from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.entities.user import UserEntity
from app.domain.enums import UserStatus
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
        stmt = select(UserModel).where(
            UserModel.tenant_id == tenant_id.value,
            UserModel.deleted_at.is_(None),
        )
        
        # Apply filters
        if status:
            stmt = stmt.where(UserModel.status == status)
        if is_email_verified is not None:
            if is_email_verified:
                stmt = stmt.where(UserModel.email_verified_at.isnot(None))
            else:
                stmt = stmt.where(UserModel.email_verified_at.is_(None))
        if search:
            search_pattern = f"%{search.lower()}%"
            stmt = stmt.where(UserModel.email.ilike(search_pattern))
        
        # Apply sorting
        sort_column = getattr(UserModel, sort_by, UserModel.created_at)
        if sort_desc:
            stmt = stmt.order_by(sort_column.desc())
        else:
            stmt = stmt.order_by(sort_column.asc())
        
        # Apply pagination
        stmt = stmt.limit(limit).offset(offset)
        
        result = await self.session.execute(stmt)
        models = result.scalars().all()
        
        return [UserMapper.to_entity(model) for model in models]
    
    async def count(
        self,
        tenant_id: TenantId,
        status: UserStatus | None = None,
        is_email_verified: bool | None = None,
        search: str | None = None,
    ) -> int:
        """Count users matching filters."""
        stmt = select(func.count(UserModel.id)).where(
            UserModel.tenant_id == tenant_id.value,
            UserModel.deleted_at.is_(None),
        )
        
        # Apply filters
        if status:
            stmt = stmt.where(UserModel.status == status)
        if is_email_verified is not None:
            if is_email_verified:
                stmt = stmt.where(UserModel.email_verified_at.isnot(None))
            else:
                stmt = stmt.where(UserModel.email_verified_at.is_(None))
        if search:
            search_pattern = f"%{search.lower()}%"
            stmt = stmt.where(UserModel.email.ilike(search_pattern))
        
        result = await self.session.execute(stmt)
        return int(result.scalar() or 0)
