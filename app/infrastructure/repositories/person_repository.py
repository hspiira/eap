"""
Person Repository Implementation

SQLAlchemy implementation of PersonRepository interface.
Uses TenantScopedRepositoryImpl base class where possible, but requires
UserRepository to load the profile (special dependency).
"""

from collections.abc import Sequence
from typing import Any

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
from app.infrastructure.repositories.base import TenantScopedRepositoryImpl


class PersonRepositoryImpl(TenantScopedRepositoryImpl[PersonEntity, PersonModel, PersonId], PersonRepository):
    """
    SQLAlchemy implementation of PersonRepository.

    Partially inherits from TenantScopedRepositoryImpl, but overrides
    get_by_id and related methods because Person requires loading the
    associated User profile.
    """

    model_class = PersonModel
    id_column = "id"

    def __init__(self, session: AsyncSession, user_repository: UserRepository) -> None:
        """
        Initialize repository with database session and user repository.

        Args:
            session: SQLAlchemy async database session
            user_repository: UserRepository to load user profiles
        """
        super().__init__(session)
        self.user_repository = user_repository

    def _to_entity(self, model: PersonModel) -> PersonEntity:
        """Convert model to entity - NOT USED directly, use _to_entity_with_profile."""
        raise NotImplementedError("Use _to_entity_with_profile for Person")

    def _to_model(self, entity: PersonEntity) -> PersonModel:
        """Convert entity to model."""
        return PersonMapper.to_model(entity)

    def _get_id_value(self, entity_id: PersonId) -> Any:
        """Extract raw ID value."""
        return entity_id.value

    async def _to_entity_with_profile(self, model: PersonModel) -> PersonEntity | None:
        """Convert model to entity, loading the user profile."""
        user_id = UserId(model.user_id)
        profile = await self.user_repository.get_by_id(user_id)
        if not profile:
            return None
        return PersonMapper.to_entity(model, profile)

    # Override base methods to load profile

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

        return await self._to_entity_with_profile(model)

    # Domain-specific queries

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

        return await self._to_entity_with_profile(model)

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
            entity = await self._to_entity_with_profile(model)
            if entity:
                entities.append(entity)

        return entities

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

        ALLOWED_SORT_COLUMNS = {"created_at", "updated_at", "status", "person_type"}
        if sort_by not in ALLOWED_SORT_COLUMNS:
            raise ValueError(f"Invalid sort column: {sort_by}") 
        if sort_desc:
            stmt = stmt.order_by(getattr(PersonModel, sort_by).desc())
        else:
            stmt = stmt.order_by(getattr(PersonModel, sort_by).asc())

        # Apply pagination
        stmt = stmt.limit(limit).offset(offset)

        result = await self.session.execute(stmt)
        models = result.scalars().all()

        entities = []
        for model in models:
            entity = await self._to_entity_with_profile(model)
            if entity:
                entities.append(entity)

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
