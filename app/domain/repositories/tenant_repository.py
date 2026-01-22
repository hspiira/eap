"""
Tenant Repository Interface

Defines the contract for Tenant data access.
Implementation lives in infrastructure layer.
"""

from abc import abstractmethod
from typing import Sequence

from app.domain.entities.tenant import TenantEntity
from app.domain.enums import SubscriptionTier, TenantStatus
from app.domain.repositories.base_repository import BaseRepository
from app.domain.value_objects.core import TenantCode, TenantId


class TenantRepository(BaseRepository[TenantEntity, TenantId]):
    """
    Repository interface for Tenant aggregate.
    
    Repositories are ONLY for aggregate roots.
    This interface is in the domain layer - implementation in infrastructure.
    """
    
    @abstractmethod
    async def get_by_code(self, code: str) -> TenantEntity | None:
        """
        Get tenant by code string.
        
        Args:
            code: Tenant code string
            
        Returns:
            TenantEntity if found, None otherwise
        """
    
    @abstractmethod
    async def list_all(
        self,
        status: TenantStatus | None = None,
        subscription_tier: SubscriptionTier | None = None,
        search: str | None = None,
        limit: int = 100,
        offset: int = 0,
        sort_by: str = "created_at",
        sort_desc: bool = True,
    ) -> Sequence[TenantEntity]:
        """
        List tenants with filtering, searching, and pagination.
        
        Args:
            status: Filter by tenant status
            subscription_tier: Filter by subscription tier
            search: Search in name or code
            limit: Maximum number of results
            offset: Number of results to skip
            sort_by: Field to sort by
            sort_desc: Sort in descending order
            
        Returns:
            Sequence of TenantEntity
        """
    
    @abstractmethod
    async def count(
        self,
        status: TenantStatus | None = None,
        subscription_tier: SubscriptionTier | None = None,
        search: str | None = None,
    ) -> int:
        """
        Count tenants matching filters.
        
        Args:
            status: Filter by tenant status
            subscription_tier: Filter by subscription tier
            search: Search in name or code
            
        Returns:
            Total count
        """
