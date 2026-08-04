"""
Person Repository Interface

Defines the contract for Person data access.
Implementation lives in infrastructure layer.
"""

from abc import abstractmethod
from collections.abc import Sequence

from app.domain.entities.person import PersonEntity
from app.domain.enums import BaseStatus, PersonType
from app.domain.repositories.base_repository import BaseRepository
from app.domain.value_objects.core import ClientId, PersonId, TenantId, UserId


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
    async def get_by_type(self, tenant_id: TenantId, person_type: PersonType) -> list[PersonEntity]:
        """
        Get all persons of a specific type within a tenant.

        Args:
            tenant_id: Tenant identifier
            person_type: Person type to filter by

        Returns:
            List of PersonEntity matching the type
        """

    @abstractmethod
    async def list_all(
        self,
        tenant_id: TenantId,
        status: BaseStatus | None = None,
        person_type: PersonType | None = None,
        client_id: ClientId | None = None,
        search: str | None = None,
        limit: int = 100,
        offset: int = 0,
        sort_by: str = "created_at",
        sort_desc: bool = True,
    ) -> Sequence[PersonEntity]:
        """
        List persons with filtering, searching, and pagination.

        Args:
            tenant_id: Tenant identifier
            status: Filter by person status
            person_type: Filter by person type
            client_id: Filter by client ID (persons whose employment_info.client_id matches)
            search: Search in user profile (name, email)
            limit: Maximum number of results
            offset: Number of results to skip
            sort_by: Field to sort by
            sort_desc: Sort in descending order

        Returns:
            Sequence of PersonEntity
        """

    @abstractmethod
    async def count(
        self,
        tenant_id: TenantId,
        status: BaseStatus | None = None,
        person_type: PersonType | None = None,
        client_id: ClientId | None = None,
        search: str | None = None,
    ) -> int:
        """
        Count persons matching filters.

        Args:
            tenant_id: Tenant identifier
            status: Filter by person status
            person_type: Filter by person type
            client_id: Filter by client ID (persons whose employment_info.client_id matches)
            search: Search in user profile

        Returns:
            Total count
        """
