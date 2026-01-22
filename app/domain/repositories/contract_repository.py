"""
Contract Repository Interface

Defines the contract for Contract data access.
Implementation lives in infrastructure layer.
"""

from abc import abstractmethod

from app.domain.entities.contract import ContractEntity
from app.domain.repositories.base_repository import BaseRepository
from app.domain.value_objects.core import ClientId, ContractId, TenantId


class ContractRepository(BaseRepository[ContractEntity, ContractId]):
    """
    Repository interface for Contract aggregate.

    Repositories are ONLY for aggregate roots.
    This interface is in the domain layer - implementation in infrastructure.
    """

    @abstractmethod
    async def get_by_client_id(
        self, tenant_id: TenantId, client_id: ClientId
    ) -> list[ContractEntity]:
        """
        Get all contracts for a client within a tenant.

        Args:
            tenant_id: Tenant identifier
            client_id: Client identifier

        Returns:
            List of ContractEntity for the client
        """
        pass

    @abstractmethod
    async def get_active_by_client_id(
        self, tenant_id: TenantId, client_id: ClientId
    ) -> ContractEntity | None:
        """
        Get active contract for a client within a tenant.

        Args:
            tenant_id: Tenant identifier
            client_id: Client identifier

        Returns:
            Active ContractEntity if found, None otherwise
        """
        pass
