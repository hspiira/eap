"""
Industry Use Cases

Application services for Industry aggregate operations.
"""

from app.domain.entities.industry import IndustryEntity
from app.domain.repositories.industry_repository import IndustryRepository
from app.domain.value_objects.core import IndustryId, TenantId
from app.shared.utils.datetime import utc_now


class CreateIndustryUseCase:
    """Use case for creating a new industry."""

    def __init__(self, industry_repository: IndustryRepository):
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
        """
        Create a new industry.

        Args:
            industry_id: Unique industry identifier
            tenant_id: Tenant identifier
            name: Industry name
            description: Industry description (optional)
            code: Industry code (optional)
            parent_industry_id: Parent industry ID (optional)

        Returns:
            Created IndustryEntity

        Raises:
            ValueError: If validation fails
        """
        # Check if industry with same name already exists
        existing = await self.industry_repository.get_by_name(name, tenant_id)
        if existing:
            raise ValueError(f"Industry with name '{name}' already exists")

        # Validate parent exists if provided
        if parent_industry_id:
            parent = await self.industry_repository.get_by_id(parent_industry_id)
            if not parent:
                raise ValueError(f"Parent industry {parent_industry_id.value} not found")

        # Create industry entity
        industry = IndustryEntity(
            _id=industry_id,
            _tenant_id=tenant_id,
            _name=name,
            _description=description,
            _code=code,
            _parent_industry_id=parent_industry_id,
            _is_active=True,
            _created_at=utc_now(),
            _updated_at=utc_now(),
        )

        # Save industry
        await self.industry_repository.save(industry)

        return industry


class UpdateIndustryUseCase:
    """Use case for updating an industry."""

    def __init__(self, industry_repository: IndustryRepository):
        self.industry_repository = industry_repository

    async def execute(
        self,
        industry_id: IndustryId,
        name: str | None = None,
        description: str | None = None,
        code: str | None = None,
        parent_industry_id: IndustryId | None = None,
    ) -> IndustryEntity:
        """
        Update an industry.

        Args:
            industry_id: Industry identifier
            name: Industry name (optional)
            description: Industry description (optional)
            code: Industry code (optional)
            parent_industry_id: Parent industry ID (optional)

        Returns:
            Updated IndustryEntity

        Raises:
            ValueError: If industry not found
            DomainError: If update is invalid
        """
        industry = await self.industry_repository.get_by_id(industry_id)
        if not industry:
            raise ValueError(f"Industry {industry_id.value} not found")

        # Check name uniqueness if name is being updated
        if name and name != industry._name:
            existing = await self.industry_repository.get_by_name(name, industry._tenant_id)
            if existing:
                raise ValueError(f"Industry with name '{name}' already exists")

        # Validate parent exists if provided
        if parent_industry_id:
            parent = await self.industry_repository.get_by_id(parent_industry_id)
            if not parent:
                raise ValueError(f"Parent industry {parent_industry_id.value} not found")

        # Update fields
        if name:
            industry.update_name(name)
        if description is not None:
            industry.update_description(description)
        if code is not None:
            industry._code = code
            industry._updated_at = utc_now()
        if parent_industry_id is not None:
            industry.set_parent(parent_industry_id)

        await self.industry_repository.save(industry)

        return industry


class ActivateIndustryUseCase:
    """Use case for activating an industry."""

    def __init__(self, industry_repository: IndustryRepository):
        self.industry_repository = industry_repository

    async def execute(self, industry_id: IndustryId) -> IndustryEntity:
        """
        Activate an industry.

        Args:
            industry_id: Industry identifier

        Returns:
            Activated IndustryEntity

        Raises:
            ValueError: If industry not found
            DomainError: If activation is invalid
        """
        industry = await self.industry_repository.get_by_id(industry_id)
        if not industry:
            raise ValueError(f"Industry {industry_id.value} not found")

        industry.activate()
        await self.industry_repository.save(industry)

        return industry


class DeactivateIndustryUseCase:
    """Use case for deactivating an industry."""

    def __init__(self, industry_repository: IndustryRepository):
        self.industry_repository = industry_repository

    async def execute(self, industry_id: IndustryId) -> IndustryEntity:
        """
        Deactivate an industry.

        Args:
            industry_id: Industry identifier

        Returns:
            Deactivated IndustryEntity

        Raises:
            ValueError: If industry not found
            DomainError: If deactivation is invalid
        """
        industry = await self.industry_repository.get_by_id(industry_id)
        if not industry:
            raise ValueError(f"Industry {industry_id.value} not found")

        industry.deactivate()
        await self.industry_repository.save(industry)

        return industry


class GetIndustryUseCase:
    """Use case for retrieving an industry."""

    def __init__(self, industry_repository: IndustryRepository):
        self.industry_repository = industry_repository

    async def execute(self, industry_id: IndustryId) -> IndustryEntity | None:
        """
        Get industry by ID.

        Args:
            industry_id: Industry identifier

        Returns:
            IndustryEntity if found, None otherwise
        """
        return await self.industry_repository.get_by_id(industry_id)
