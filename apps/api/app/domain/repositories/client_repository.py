"""
Client Repository Interface

Defines the contract for Client data access.
Implementation lives in infrastructure layer.
"""

from abc import abstractmethod
from collections.abc import Sequence

from app.domain.entities.client import ClientEntity
from app.domain.enums import BaseStatus
from app.domain.repositories.base_repository import BaseRepository
from app.domain.value_objects.core import ClientId, TenantId


class ClientRepository(BaseRepository[ClientEntity, ClientId]):
    """
    Repository interface for Client aggregate.

    Repositories are ONLY for aggregate roots.
    This interface is in the domain layer - implementation in infrastructure.
    """

    @abstractmethod
    async def get_by_name(self, tenant_id: TenantId, name: str) -> ClientEntity | None:
        """
        Get client by name within a tenant.

        Args:
            tenant_id: Tenant identifier
            name: Client name

        Returns:
            ClientEntity if found, None otherwise
        """

    @abstractmethod
    async def get_by_name_or_alias(self, tenant_id: TenantId, value: str) -> ClientEntity | None:
        """Get a client by canonical name or normalized alias."""

    @abstractmethod
    async def get_by_code(self, tenant_id: TenantId, code: str) -> ClientEntity | None:
        """Get a client by normalized code within a tenant."""

    @abstractmethod
    async def list_all(
        self,
        tenant_id: TenantId,
        status: BaseStatus | None = None,
        is_verified: bool | None = None,
        tier: str | None = None,
        parent_client_id: ClientId | None = None,
        include_archived: bool = False,
        search: str | None = None,
        limit: int = 100,
        offset: int = 0,
        sort_by: str = "created_at",
        sort_desc: bool = True,
    ) -> Sequence[ClientEntity]:
        """List clients with filtering, searching, and pagination."""

    @abstractmethod
    async def count(
        self,
        tenant_id: TenantId,
        status: BaseStatus | None = None,
        is_verified: bool | None = None,
        tier: str | None = None,
        parent_client_id: ClientId | None = None,
        include_archived: bool = False,
        search: str | None = None,
    ) -> int:
        """Count clients matching filters."""
