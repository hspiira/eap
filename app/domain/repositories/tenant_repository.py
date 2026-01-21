"""
Tenant Repository Interface

Defines the contract for Tenant data access.
Implementation lives in infrastructure layer.
"""

from abc import ABC, abstractmethod
from app.domain.entities.tenant import TenantEntity
from app.domain.value_objects.core import TenantId


class TenantRepository(ABC):
    """
    Repository interface for Tenant aggregate.
    
    Repositories are ONLY for aggregate roots.
    This interface is in the domain layer - implementation in infrastructure.
    """
    
    @abstractmethod
    def get_by_id(self, tenant_id: TenantId) -> TenantEntity | None:
        """
        Get tenant by ID.
        
        Args:
            tenant_id: Tenant identifier
            
        Returns:
            TenantEntity if found, None otherwise
        """
        pass
    
    @abstractmethod
    def get_by_code(self, code: str) -> TenantEntity | None:
        """
        Get tenant by code.
        
        Args:
            code: Tenant code
            
        Returns:
            TenantEntity if found, None otherwise
        """
        pass
    
    @abstractmethod
    def save(self, tenant: TenantEntity) -> None:
        """
        Save tenant aggregate.
        
        This should save the entire aggregate atomically.
        Domain events are handled separately by the application service.
        
        Args:
            tenant: TenantEntity to save
        """
        pass
    
    @abstractmethod
    def delete(self, tenant_id: TenantId) -> None:
        """
        Soft delete tenant.
        
        Args:
            tenant_id: Tenant identifier
        """
        pass
    
    @abstractmethod
    def exists(self, tenant_id: TenantId) -> bool:
        """
        Check if tenant exists.
        
        Args:
            tenant_id: Tenant identifier
            
        Returns:
            True if tenant exists, False otherwise
        """
        pass
