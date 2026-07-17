"""
User Repository Interface

Defines the contract for User data access.
Implementation lives in infrastructure layer.
"""

from abc import abstractmethod
from collections.abc import Sequence

from app.domain.entities.user import UserEntity
from app.domain.enums import UserStatus
from app.domain.repositories.base_repository import BaseRepository
from app.domain.value_objects.core import Email, TenantId, UserId


class UserRepository(BaseRepository[UserEntity, UserId]):
    """
    Repository interface for User aggregate.

    Repositories are ONLY for aggregate roots.
    This interface is in the domain layer - implementation in infrastructure.
    """

    @abstractmethod
    async def get_by_email(self, email: Email, tenant_id: TenantId) -> UserEntity | None:
        """
        Get user by email address object within a tenant.

        Args:
            email: User email address object
            tenant_id: Tenant identifier object

        Returns:
            UserEntity if found, None otherwise
        """
    
    @abstractmethod
    async def list_all(
        self,
        tenant_id: TenantId,
        status: UserStatus | None = None,
        is_email_verified: bool | None = None,
        is_two_factor_enabled: bool | None = None,
        search: str | None = None,
        limit: int = 100,
        offset: int = 0,
        sort_by: str = "created_at",
        sort_desc: bool = True,
    ) -> Sequence[UserEntity]:
        """
        List users with filtering, searching, and pagination.

        Args:
            tenant_id: Tenant identifier
            status: Filter by user status
            is_email_verified: Filter by email verification status
            is_two_factor_enabled: Filter by two-factor enrolment
            search: Search in user email
            limit: Maximum number of results
            offset: Number of results to skip
            sort_by: Field to sort by
            sort_desc: Sort in descending order

        Returns:
            Sequence of UserEntity
        """
    
    @abstractmethod
    async def count(
        self,
        tenant_id: TenantId,
        status: UserStatus | None = None,
        is_email_verified: bool | None = None,
        is_two_factor_enabled: bool | None = None,
        search: str | None = None,
    ) -> int:
        """
        Count users matching filters.

        Must apply exactly the same filters as `list_all` — a count that disagrees
        with its page produces pagination over a total the caller cannot reach.

        Args:
            tenant_id: Tenant identifier
            status: Filter by user status
            is_email_verified: Filter by email verification status
            is_two_factor_enabled: Filter by two-factor enrolment
            search: Search in user email

        Returns:
            Total count
        """

    @abstractmethod
    async def get_by_azure_oid(self, azure_oid: str, tenant_id: TenantId) -> UserEntity | None:
        """
        Get a user by their Azure Object ID within a tenant.

        Args:
            azure_oid: The Azure AD object ID (oid claim from Azure token)
            tenant_id: Tenant identifier

        Returns:
            UserEntity if found and not soft-deleted, None otherwise
        """

    @abstractmethod
    async def update_password(self, user_id: UserId, password_hash: str) -> bool:
        """
        Update a user's password hash (e.g. after set-initial-password).

        Args:
            user_id: User identifier
            password_hash: New hashed password

        Returns:
            True if user was found and updated, False otherwise
        """
