"""
Person Repository Implementation

SQLAlchemy implementation of PersonRepository interface.
"""

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.entities.person import PersonEntity
from app.domain.enums import PersonType
from app.domain.repositories.person_repository import PersonRepository
from app.domain.repositories.user_repository import UserRepository
from app.domain.value_objects.core import PersonId, TenantId, UserId
from app.infrastructure.mappers.person_mapper import PersonMapper
from app.infrastructure.models.person_model import PersonModel


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
            PersonModel.person_type == person_type.value,
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
        stmt = select(PersonModel).where(PersonModel.id == person_id.value)
        result = await self.session.execute(stmt)
        model = result.scalar_one_or_none()

        if model:
            from app.shared.utils.datetime import utc_now

            model.deleted_at = utc_now()
            await self.session.merge(model)

    async def exists(self, person_id: PersonId) -> bool:
        """Check if person exists (not soft-deleted)."""
        stmt = select(PersonModel).where(
            PersonModel.id == person_id.value,
            PersonModel.deleted_at.is_(None),
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none() is not None
