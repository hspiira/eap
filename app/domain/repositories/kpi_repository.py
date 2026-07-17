"""
KPI Repository Interface

Defines the contract for KPI data access.
Implementation lives in infrastructure layer.
"""

from abc import abstractmethod
from collections.abc import Sequence

from app.domain.entities.kpi import KPIAssignmentEntity, KPIEntity
from app.domain.enums import KPICategory
from app.domain.repositories.base_repository import BaseRepository
from app.domain.value_objects.core import KPIAssignmentId, KPIId, TenantId


class KPIRepository(BaseRepository[KPIEntity, KPIId]):
    """
    Repository interface for KPI aggregate.

    Repositories are ONLY for aggregate roots.
    This interface is in the domain layer - implementation in infrastructure.
    """

    @abstractmethod
    async def get_by_name(
        self, name: str, tenant_id: TenantId
    ) -> KPIEntity | None:
        """
        Get KPI by name within a tenant.
        
        Args:
            name: KPI name
            tenant_id: Tenant identifier
            
        Returns:
            KPIEntity if found, None otherwise
        """
    
    @abstractmethod
    async def list_all(
        self,
        tenant_id: TenantId,
        category: KPICategory | None = None,
        is_active: bool | None = None,
        search: str | None = None,
        limit: int = 100,
        offset: int = 0,
        sort_by: str = "created_at",
        sort_desc: bool = True,
    ) -> Sequence[KPIEntity]:
        """
        List KPIs with filtering, searching, and pagination.
        
        Args:
            tenant_id: Tenant identifier
            category: Filter by KPI category
            is_active: Filter by active status
            search: Search in KPI name or description
            limit: Maximum number of results
            offset: Number of results to skip
            sort_by: Field to sort by
            sort_desc: Sort in descending order
            
        Returns:
            Sequence of KPIEntity
        """
    
    @abstractmethod
    async def count(
        self,
        tenant_id: TenantId,
        category: KPICategory | None = None,
        is_active: bool | None = None,
        search: str | None = None,
    ) -> int:
        """
        Count KPIs matching filters.
        
        Args:
            tenant_id: Tenant identifier
            category: Filter by KPI category
            is_active: Filter by active status
            search: Search in KPI name or description
            
        Returns:
            Total count
        """


class KPIAssignmentRepository(BaseRepository[KPIAssignmentEntity, KPIAssignmentId]):
    """
    Repository interface for KPI Assignment aggregate.
    """

    @abstractmethod
    async def get_by_kpi_id(
        self, kpi_id: KPIId, tenant_id: TenantId
    ) -> Sequence[KPIAssignmentEntity]:
        """
        Get all assignments for a KPI.
        
        Args:
            kpi_id: KPI identifier
            tenant_id: Tenant identifier
            
        Returns:
            Sequence of KPIAssignmentEntity
        """
    
    @abstractmethod
    async def get_by_client_id(
        self, client_id: str, tenant_id: TenantId
    ) -> Sequence[KPIAssignmentEntity]:
        """
        Get all assignments for a client.
        
        Args:
            client_id: Client identifier
            tenant_id: Tenant identifier
            
        Returns:
            Sequence of KPIAssignmentEntity
        """
    
    @abstractmethod
    async def get_by_contract_id(
        self, contract_id: str, tenant_id: TenantId
    ) -> Sequence[KPIAssignmentEntity]:
        """
        Get all assignments for a contract.
        
        Args:
            contract_id: Contract identifier
            tenant_id: Tenant identifier
            
        Returns:
            Sequence of KPIAssignmentEntity
        """
    
    @abstractmethod
    async def list_all(
        self,
        tenant_id: TenantId,
        kpi_id: KPIId | None = None,
        client_id: str | None = None,
        contract_id: str | None = None,
        is_active: bool | None = None,
        limit: int = 100,
        offset: int = 0,
        sort_by: str = "created_at",
        sort_desc: bool = True,
    ) -> Sequence[KPIAssignmentEntity]:
        """
        List assignments with filtering and pagination.
        
        Args:
            tenant_id: Tenant identifier
            kpi_id: Filter by KPI
            client_id: Filter by client
            contract_id: Filter by contract
            is_active: Filter by active status
            limit: Maximum number of results
            offset: Number of results to skip
            sort_by: Field to sort by
            sort_desc: Sort in descending order
            
        Returns:
            Sequence of KPIAssignmentEntity
        """
    
    @abstractmethod
    async def count(
        self,
        tenant_id: TenantId,
        kpi_id: KPIId | None = None,
        client_id: str | None = None,
        contract_id: str | None = None,
        is_active: bool | None = None,
    ) -> int:
        """
        Count assignments matching filters.
        
        Args:
            tenant_id: Tenant identifier
            kpi_id: Filter by KPI
            client_id: Filter by client
            contract_id: Filter by contract
            is_active: Filter by active status
            
        Returns:
            Total count
        """
