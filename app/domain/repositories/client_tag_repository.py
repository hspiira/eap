"""
ClientTag Repository Interface

Defines the contract for ClientTag data access.
"""

from abc import abstractmethod
from collections.abc import Sequence

from app.domain.entities.client_tag import ClientTagEntity
from app.domain.repositories.base_repository import BaseRepository
from app.domain.value_objects.core import ClientTagId, TenantId


class ClientTagRepository(BaseRepository[ClientTagEntity, ClientTagId]):
    """Repository interface for ClientTag aggregate."""

    @abstractmethod
    async def get_by_name(self, name: str, tenant_id: TenantId) -> ClientTagEntity | None:
        """Get tag by name within a tenant."""

    @abstractmethod
    async def list_all(
        self,
        tenant_id: TenantId,
        is_active: bool | None = None,
        search: str | None = None,
        limit: int = 100,
        offset: int = 0,
    ) -> Sequence[ClientTagEntity]:
        """List tags with filtering."""

    @abstractmethod
    async def count(
        self,
        tenant_id: TenantId,
        is_active: bool | None = None,
        search: str | None = None,
    ) -> int:
        """Count tags matching filters."""
