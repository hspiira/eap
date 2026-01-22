"""
Tenant Repository Interface

Defines the contract for Tenant data access.
Implementation lives in infrastructure layer.
"""

from abc import abstractmethod

from app.domain.entities.tenant import TenantEntity
from app.domain.repositories.base_repository import BaseRepository
from app.domain.value_objects.core import TenantCode, TenantId


class TenantRepository(BaseRepository[TenantEntity, TenantId]):
    """
    Repository interface for Tenant aggregate.
    
    Repositories are ONLY for aggregate roots.
    This interface is in the domain layer - implementation in infrastructure.
    """
    
    @abstractmethod
    async def get_by_code(self, code: TenantCode) -> TenantEntity | None:
        """
        Get tenant by code object.
        
        Args:
            code: Tenant code object
            
        Returns:
            TenantEntity if found, None otherwise
        """
