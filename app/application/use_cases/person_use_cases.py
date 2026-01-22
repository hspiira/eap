"""
Person Use Cases

Application services for Person aggregate operations.
"""

from typing import TYPE_CHECKING

from app.domain.entities.person import PersonEntity
from app.domain.enums import PersonType
from app.domain.repositories.person_repository import PersonRepository
from app.domain.value_objects.core import PersonId, TenantId, UserId
from app.shared.utils.datetime import utc_now

if TYPE_CHECKING:
    from app.domain.entities.user import UserEntity
    from app.domain.value_objects.core import EmploymentInfo


class CreateClientEmployeeUseCase:
    """Use case for creating a client employee person."""

    def __init__(self, person_repository: PersonRepository):
        self.person_repository = person_repository

    async def execute(
        self,
        person_id: PersonId,
        tenant_id: TenantId,
        user_id: UserId,
        profile: "UserEntity",
        employment_info: "EmploymentInfo",
    ) -> PersonEntity:
        """
        Create a new client employee person.

        Args:
            person_id: Unique person identifier
            tenant_id: Tenant identifier
            user_id: User identifier
            profile: UserEntity profile
            employment_info: Employment information

        Returns:
            Created PersonEntity

        Raises:
            ValueError: If person already exists
        """
        # Check if person already exists for this user
        existing = await self.person_repository.get_by_user_id(user_id)
        if existing:
            raise ValueError(f"Person already exists for user {user_id.value}")

        # Create person entity using factory method
        person = PersonEntity.create_client_employee(
            id=person_id,
            tenant_id=tenant_id,
            user_id=user_id,
            profile=profile,
            employment_info=employment_info,
        )

        # Save person
        await self.person_repository.save(person)

        return person


class ActivatePersonUseCase:
    """Use case for activating a person."""

    def __init__(self, person_repository: PersonRepository):
        self.person_repository = person_repository

    async def execute(self, person_id: PersonId) -> PersonEntity:
        """
        Activate a person.

        Args:
            person_id: Person identifier

        Returns:
            Activated PersonEntity

        Raises:
            ValueError: If person not found
        """
        person = await self.person_repository.get_by_id(person_id)
        if not person:
            raise ValueError(f"Person {person_id.value} not found")

        person.activate()
        person._updated_at = utc_now()
        await self.person_repository.save(person)

        return person


class GetPersonUseCase:
    """Use case for retrieving a person."""

    def __init__(self, person_repository: PersonRepository):
        self.person_repository = person_repository

    async def execute(self, person_id: PersonId) -> PersonEntity | None:
        """
        Get person by ID.

        Args:
            person_id: Person identifier

        Returns:
            PersonEntity if found, None otherwise
        """
        return await self.person_repository.get_by_id(person_id)

    async def execute_by_user_id(self, user_id: UserId) -> PersonEntity | None:
        """
        Get person by user ID.

        Args:
            user_id: User identifier

        Returns:
            PersonEntity if found, None otherwise
        """
        return await self.person_repository.get_by_user_id(user_id)


class GetPersonsByTypeUseCase:
    """Use case for retrieving persons by type."""

    def __init__(self, person_repository: PersonRepository):
        self.person_repository = person_repository

    async def execute(
        self, tenant_id: TenantId, person_type: PersonType
    ) -> list[PersonEntity]:
        """
        Get all persons of a specific type within a tenant.

        Args:
            tenant_id: Tenant identifier
            person_type: Person type to filter by

        Returns:
            List of PersonEntity matching the type
        """
        return await self.person_repository.get_by_type(tenant_id, person_type)
