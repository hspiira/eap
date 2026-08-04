"""
Industry Repository Interface

Defines the contract for Industry data access.
"""

from abc import abstractmethod
from collections.abc import Sequence

from app.domain.entities.industry import IndustryEntity
from app.domain.repositories.base_repository import BaseRepository
from app.domain.value_objects.core import IndustryId, TenantId


class IndustryRepository(BaseRepository[IndustryEntity, IndustryId]):
    """Repository interface for Industry aggregate."""

    @abstractmethod
    async def get_by_name(self, name: str, tenant_id: TenantId) -> IndustryEntity | None:
        """Get industry by name within a tenant."""

    @abstractmethod
    async def get_by_code(self, code: str, tenant_id: TenantId) -> IndustryEntity | None:
        """Get industry by code within a tenant."""

    @abstractmethod
    async def get_children(
        self, parent_id: IndustryId, tenant_id: TenantId
    ) -> Sequence[IndustryEntity]:
        """Get child industries for a parent."""

    @abstractmethod
    async def list_all(
        self,
        tenant_id: TenantId,
        parent_id: IndustryId | None = None,
        is_active: bool | None = None,
        search: str | None = None,
        limit: int = 100,
        offset: int = 0,
    ) -> Sequence[IndustryEntity]:
        """List industries with filtering."""

    @abstractmethod
    async def count(
        self,
        tenant_id: TenantId,
        parent_id: IndustryId | None = None,
        is_active: bool | None = None,
        search: str | None = None,
    ) -> int:
        """Count industries matching filters."""
