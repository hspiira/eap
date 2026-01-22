"""
Client Repository Interface

Defines the contract for Client data access.
Implementation lives in infrastructure layer.
"""

from abc import abstractmethod

from app.domain.entities.client import ClientEntity
from app.domain.repositories.base_repository import BaseRepository
from app.domain.value_objects.core import ClientId, TenantId


class ClientRepository(BaseRepository[ClientEntity, ClientId]):
    """
    Repository interface for Client aggregate.

    Repositories are ONLY for aggregate roots.
    This interface is in the domain layer - implementation in infrastructure.
    """

    @abstractmethod
    async def get_by_name(
        self, tenant_id: TenantId, name: str
    ) -> ClientEntity | None:
        """
        Get client by name within a tenant.

        Args:
            tenant_id: Tenant identifier
            name: Client name

        Returns:
            ClientEntity if found, None otherwise
        """
