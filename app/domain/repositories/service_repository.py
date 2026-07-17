"""
Service Repository Interface

Defines the contract for Service data access.
Implementation lives in infrastructure layer.
"""

from abc import abstractmethod
from collections.abc import Sequence

from app.domain.entities.service import ServiceEntity
from app.domain.enums import BaseStatus
from app.domain.repositories.base_repository import BaseRepository
from app.domain.value_objects.core import ServiceId, TenantId


class ServiceRepository(BaseRepository[ServiceEntity, ServiceId]):
    """
    Repository interface for Service aggregate.

    Repositories are ONLY for aggregate roots.
    This interface is in the domain layer - implementation in infrastructure.
    """

    @abstractmethod
    async def get_by_name(
        self, tenant_id: TenantId, name: str
    ) -> ServiceEntity | None:
        """
        Get service by name within a tenant.

        Args:
            tenant_id: Tenant identifier
            name: Service name

        Returns:
            ServiceEntity if found, None otherwise
        """
        pass

    @abstractmethod
    async def list_all(
        self,
        tenant_id: TenantId,
        status: BaseStatus | None = None,
        category: str | None = None,
        is_group_service: bool | None = None,
        search: str | None = None,
        limit: int = 100,
        offset: int = 0,
        sort_by: str = "created_at",
        sort_desc: bool = True,
    ) -> Sequence[ServiceEntity]:
        """
        List services with filtering, searching, and pagination.
        
        Args:
            tenant_id: Tenant identifier
            status: Filter by service status
            category: Filter by service category
            is_group_service: Filter by group service flag
            search: Search in service name or description
            limit: Maximum number of results
            offset: Number of results to skip
            sort_by: Field to sort by
            sort_desc: Sort in descending order
            
        Returns:
            Sequence of ServiceEntity
        """
    
    @abstractmethod
    async def count(
        self,
        tenant_id: TenantId,
        status: BaseStatus | None = None,
        category: str | None = None,
        is_group_service: bool | None = None,
        search: str | None = None,
    ) -> int:
        """
        Count services matching filters.
        
        Args:
            tenant_id: Tenant identifier
            status: Filter by service status
            category: Filter by service category
            is_group_service: Filter by group service flag
            search: Search in service name or description
            
        Returns:
            Total count
        """
