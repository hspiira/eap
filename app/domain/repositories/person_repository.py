"""
Person Repository Interface

Defines the contract for Person data access.
Implementation lives in infrastructure layer.
"""

from abc import abstractmethod

from app.domain.entities.person import PersonEntity
from app.domain.enums import PersonType
from app.domain.repositories.base_repository import BaseRepository
from app.domain.value_objects.core import PersonId, TenantId, UserId


class PersonRepository(BaseRepository[PersonEntity, PersonId]):
    """
    Repository interface for Person aggregate.

    Repositories are ONLY for aggregate roots.
    This interface is in the domain layer - implementation in infrastructure.
    """

    @abstractmethod
    async def get_by_user_id(self, user_id: UserId) -> PersonEntity | None:
        """
        Get person by user ID.

        Args:
            user_id: User identifier

        Returns:
            PersonEntity if found, None otherwise
        """

    @abstractmethod
    async def get_by_type(
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
