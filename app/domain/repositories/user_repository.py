"""
User Repository Interface

Defines the contract for User data access.
Implementation lives in infrastructure layer.
"""

from abc import abstractmethod

from app.domain.entities.user import UserEntity
from app.domain.repositories.base_repository import BaseRepository
from app.domain.value_objects.core import TenantId, UserId


class UserRepository(BaseRepository[UserEntity, UserId]):
    """
    Repository interface for User aggregate.

    Repositories are ONLY for aggregate roots.
    This interface is in the domain layer - implementation in infrastructure.
    """

    @abstractmethod
    async def get_by_email(self, email: str, tenant_id: TenantId) -> UserEntity | None:
        """
        Get user by email within a tenant.

        Args:
            email: User email address
            tenant_id: Tenant identifier

        Returns:
            UserEntity if found, None otherwise
        """
