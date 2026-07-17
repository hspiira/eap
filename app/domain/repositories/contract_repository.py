"""
Contract Repository Interface

Defines the contract for Contract data access.
Implementation lives in infrastructure layer.
"""

from abc import abstractmethod
from datetime import datetime
from typing import Sequence

from app.domain.entities.contract import ContractEntity
from app.domain.enums import ContractStatus, PaymentStatus
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
    
    @abstractmethod
    async def list_all(
        self,
        tenant_id: TenantId,
        client_id: ClientId | None = None,
        status: ContractStatus | None = None,
        payment_status: PaymentStatus | None = None,
        is_auto_renew: bool | None = None,
        ends_from: datetime | None = None,
        ends_to: datetime | None = None,
        search: str | None = None,
        limit: int = 100,
        offset: int = 0,
        sort_by: str = "created_at",
        sort_desc: bool = True,
    ) -> Sequence[ContractEntity]:
        """
        List contracts with filtering, searching, and pagination.
        
        Args:
            tenant_id: Tenant identifier
            client_id: Filter by client identifier
            status: Filter by contract status
            payment_status: Filter by payment status
            search: Search in contract details (not implemented in basic version)
            limit: Maximum number of results
            offset: Number of results to skip
            sort_by: Field to sort by
            sort_desc: Sort in descending order
            
        Returns:
            Sequence of ContractEntity
        """
    
    @abstractmethod
    async def count(
        self,
        tenant_id: TenantId,
        client_id: ClientId | None = None,
        status: ContractStatus | None = None,
        payment_status: PaymentStatus | None = None,
        is_auto_renew: bool | None = None,
        ends_from: datetime | None = None,
        ends_to: datetime | None = None,
        search: str | None = None,
    ) -> int:
        """
        Count contracts matching filters.
        
        Args:
            tenant_id: Tenant identifier
            client_id: Filter by client identifier
            status: Filter by contract status
            payment_status: Filter by payment status
            search: Search in contract details
            
        Returns:
            Total count
        """
