"""
Person Repository Implementation

SQLAlchemy implementation of PersonRepository interface.
"""

from typing import Sequence

from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.entities.person import PersonEntity
from app.domain.enums import BaseStatus, PersonType
from app.domain.repositories.person_repository import PersonRepository
from app.domain.repositories.user_repository import UserRepository
from app.domain.value_objects.core import PersonId, TenantId, UserId
from app.infrastructure.mappers.person_mapper import PersonMapper
from app.infrastructure.models.person_model import PersonModel
from app.infrastructure.models.user_model import UserModel
from app.shared.utils.datetime import utc_now


class PersonRepositoryImpl(PersonRepository):
    """
    SQLAlchemy implementation of PersonRepository.

    Handles data access for Person aggregate.
    Uses mapper to convert between entity and model.
    Requires UserRepository to load the profile.
    """

    def __init__(self, session: AsyncSession, user_repository: UserRepository) -> None:
        """
        Initialize repository with database session and user repository.

        Args:
            session: SQLAlchemy async database session
            user_repository: UserRepository to load user profiles
        """
        self.session = session
        self.user_repository = user_repository

    async def get_by_id(self, person_id: PersonId) -> PersonEntity | None:
        """Get person by ID, excluding soft-deleted persons."""
        stmt = select(PersonModel).where(
            PersonModel.id == person_id.value,
            PersonModel.deleted_at.is_(None),
        )
        result = await self.session.execute(stmt)
        model = result.scalar_one_or_none()

        if not model:
            return None

        # Load user profile
        user_id = UserId(model.user_id)
        profile = await self.user_repository.get_by_id(user_id)
        if not profile:
            raise ValueError(f"User {user_id.value} not found for person {person_id.value}")

        return PersonMapper.to_entity(model, profile)

    async def get_by_user_id(self, user_id: UserId) -> PersonEntity | None:
        """Get person by user ID, excluding soft-deleted persons."""
        stmt = select(PersonModel).where(
            PersonModel.user_id == user_id.value,
            PersonModel.deleted_at.is_(None),
        )
        result = await self.session.execute(stmt)
        model = result.scalar_one_or_none()

        if not model:
            return None

        # Load user profile
        profile = await self.user_repository.get_by_id(user_id)
        if not profile:
            raise ValueError(f"User {user_id.value} not found")

        return PersonMapper.to_entity(model, profile)

    async def get_by_type(
        self, tenant_id: TenantId, person_type: PersonType
    ) -> list[PersonEntity]:
        """Get all persons of a specific type within a tenant."""
        stmt = select(PersonModel).where(
            PersonModel.tenant_id == tenant_id.value,
            PersonModel.person_type == person_type,
            PersonModel.deleted_at.is_(None),
        )
        result = await self.session.execute(stmt)
        models = result.scalars().all()

        entities = []
        for model in models:
            user_id = UserId(model.user_id)
            profile = await self.user_repository.get_by_id(user_id)
            if profile:
                entities.append(PersonMapper.to_entity(model, profile))

        return entities

    async def save(self, person: PersonEntity) -> None:
        """
        Save person aggregate atomically.

        Uses merge to handle both insert and update.
        """
        model = PersonMapper.to_model(person)
        await self.session.merge(model)
        # Note: commit is typically handled by the application service/unit of work

    async def delete(self, person_id: PersonId) -> None:
        """
        Soft delete person.

        In practice, this is usually done by calling person methods
        and then save(), but this method provides explicit soft delete.
        """
        stmt = select(PersonModel).where(
            PersonModel.id == person_id.value,
            PersonModel.deleted_at.is_(None),
        )
        result = await self.session.execute(stmt)
        model = result.scalar_one_or_none()

        if model:
            now = utc_now()
            model.deleted_at = now
            model.updated_at = now
            await self.session.merge(model)

    async def exists(self, person_id: PersonId) -> bool:
        """Check if person exists (not soft-deleted)."""
        from sqlalchemy import exists as sql_exists
        stmt = sql_exists().where(
            PersonModel.id == person_id.value,
            PersonModel.deleted_at.is_(None),
        ).select()
        result = await self.session.execute(stmt)
        return bool(result.scalar())
    
    async def list_all(
        self,
        tenant_id: TenantId,
        status: BaseStatus | None = None,
        person_type: PersonType | None = None,
        search: str | None = None,
        limit: int = 100,
        offset: int = 0,
        sort_by: str = "created_at",
        sort_desc: bool = True,
    ) -> Sequence[PersonEntity]:
        """List persons with filtering, searching, and pagination."""
        # Join with UserModel for search capability
        stmt = select(PersonModel).join(
            UserModel, PersonModel.user_id == UserModel.id
        ).where(
            PersonModel.tenant_id == tenant_id.value,
            PersonModel.deleted_at.is_(None),
            UserModel.deleted_at.is_(None),
        )
        
        # Apply filters
        if status:
            stmt = stmt.where(PersonModel.status == status)
        if person_type:
            stmt = stmt.where(PersonModel.person_type == person_type)
        if search:
            search_pattern = f"%{search.lower()}%"
            stmt = stmt.where(
                or_(
                    UserModel.email.ilike(search_pattern),
                )
            )
        
        # Apply sorting
        sort_column = getattr(PersonModel, sort_by, PersonModel.created_at)
        if sort_desc:
            stmt = stmt.order_by(sort_column.desc())
        else:
            stmt = stmt.order_by(sort_column.asc())
        
        # Apply pagination
        stmt = stmt.limit(limit).offset(offset)
        
        result = await self.session.execute(stmt)
        models = result.scalars().all()
        
        entities = []
        for model in models:
            user_id = UserId(model.user_id)
            profile = await self.user_repository.get_by_id(user_id)
            if profile:
                entities.append(PersonMapper.to_entity(model, profile))
        
        return entities
    
    async def count(
        self,
        tenant_id: TenantId,
        status: BaseStatus | None = None,
        person_type: PersonType | None = None,
        search: str | None = None,
    ) -> int:
        """Count persons matching filters."""
        # Join with UserModel for search capability
        stmt = select(func.count(PersonModel.id)).join(
            UserModel, PersonModel.user_id == UserModel.id
        ).where(
            PersonModel.tenant_id == tenant_id.value,
            PersonModel.deleted_at.is_(None),
            UserModel.deleted_at.is_(None),
        )
        
        # Apply filters
        if status:
            stmt = stmt.where(PersonModel.status == status)
        if person_type:
            stmt = stmt.where(PersonModel.person_type == person_type)
        if search:
            search_pattern = f"%{search.lower()}%"
            stmt = stmt.where(
                or_(
                    UserModel.email.ilike(search_pattern),
                )
            )
        
        result = await self.session.execute(stmt)
        return int(result.scalar() or 0)
