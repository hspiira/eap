"""
Industry Use Cases

Application services for Industry aggregate operations.
Refactored to use base use case classes.
"""

from app.application.use_cases.base import BaseUseCase
from app.domain.entities.industry import IndustryEntity
from app.domain.repositories.industry_repository import IndustryRepository
from app.domain.value_objects.core import IndustryId, TenantId
from app.shared.utils.datetime import utc_now


# Lifecycle dispatched via TransitionUseCase + IndustryTransition.


class CreateIndustryUseCase(BaseUseCase[IndustryEntity, IndustryId]):
    """Use case for creating a new industry."""

    def __init__(self, industry_repository: IndustryRepository):
        super().__init__(industry_repository)
        self.industry_repository = industry_repository

    async def execute(
        self,
        industry_id: IndustryId,
        tenant_id: TenantId,
        name: str,
        description: str | None = None,
        code: str | None = None,
        parent_industry_id: IndustryId | None = None,
    ) -> IndustryEntity:
        """Create a new industry."""
        # Check if industry with same name already exists
        existing = await self.industry_repository.get_by_name(name, tenant_id)
        if existing:
            raise ValueError(f"Industry with name '{name}' already exists")

        # Validate parent exists if provided
        if parent_industry_id:
            parent = await self.industry_repository.get_by_id(parent_industry_id)
            if not parent:
                raise ValueError(f"Parent industry {parent_industry_id.value} not found")
            if parent.tenant_id != tenant_id:
                raise ValueError("Parent industry must belong to the same tenant")

        # Create industry entity
        industry = IndustryEntity(
            id=industry_id,
            tenant_id=tenant_id,
            name=name,
            description=description,
            code=code,
            parent_industry_id=parent_industry_id,
            _is_active=True,
            created_at=utc_now(),
            updated_at=utc_now(),
        )

        return await self._save_and_publish_events(industry)


# =============================================================================
# UPDATE USE CASE
# =============================================================================


class UpdateIndustryUseCase(BaseUseCase[IndustryEntity, IndustryId]):
    """Use case for updating an industry."""

    def __init__(self, industry_repository: IndustryRepository):
        super().__init__(industry_repository)
        self.industry_repository = industry_repository

    async def execute(
        self,
        industry_id: IndustryId,
        name: str | None = None,
        description: str | None = None,
        code: str | None = None,
        parent_industry_id: IndustryId | None = None,
    ) -> IndustryEntity:
        """Update an industry."""
        industry = await self._get_entity_or_raise(industry_id, "Industry")

        # Check name uniqueness if name is being updated
        if name and name != industry.name:
            existing = await self.industry_repository.get_by_name(name, industry.tenant_id)
            if existing:
                raise ValueError(f"Industry with name '{name}' already exists")

        # Validate parent exists if provided
        if parent_industry_id:
            parent = await self.industry_repository.get_by_id(parent_industry_id)
            if not parent:
                raise ValueError(f"Parent industry {parent_industry_id.value} not found")
            if parent.tenant_id != industry.tenant_id:
                raise ValueError("Parent industry must belong to the same tenant")

        # Update fields
        if name:
            industry.update_name(name)
        if description is not None:
            industry.update_description(description)
        if code is not None:
            industry.update_code(code)
        if parent_industry_id is not None:
            industry.set_parent(parent_industry_id)

        return await self._save_and_publish_events(industry)


# =============================================================================
# QUERY USE CASE
# =============================================================================


class GetIndustryUseCase(BaseUseCase[IndustryEntity, IndustryId]):
    """Use case for retrieving an industry."""

    def __init__(self, industry_repository: IndustryRepository):
        super().__init__(industry_repository)

    async def execute(self, industry_id: IndustryId) -> IndustryEntity | None:
        """Get industry by ID."""
        return await self.repository.get_by_id(industry_id)
