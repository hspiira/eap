"""
Contact Repository Interface

Defines the contract for Contact data access.
"""

from abc import abstractmethod
from collections.abc import Sequence

from app.domain.entities.contact import ContactEntity
from app.domain.repositories.base_repository import BaseRepository
from app.domain.value_objects.core import ContactId, TenantId


class ContactRepository(BaseRepository[ContactEntity, ContactId]):
    """Repository interface for Contact aggregate."""

    @abstractmethod
    async def get_by_client_id(
        self, client_id: str, tenant_id: TenantId
    ) -> Sequence[ContactEntity]:
        """Get all contacts for a client."""
    
    @abstractmethod
    async def get_primary_contact(
        self, client_id: str, tenant_id: TenantId
    ) -> ContactEntity | None:
        """Get primary contact for a client."""
    
    @abstractmethod
    async def list_all(
        self,
        tenant_id: TenantId,
        client_id: str | None = None,
        is_active: bool | None = None,
        is_primary: bool | None = None,
        search: str | None = None,
        limit: int = 100,
        offset: int = 0,
    ) -> Sequence[ContactEntity]:
        """List contacts with filtering."""
    
    @abstractmethod
    async def count(
        self,
        tenant_id: TenantId,
        client_id: str | None = None,
        is_active: bool | None = None,
        is_primary: bool | None = None,
        search: str | None = None,
    ) -> int:
        """Count contacts matching filters."""
