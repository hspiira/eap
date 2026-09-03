"""
Activity Repository Interface

Defines the contract for Activity data access.
"""

from abc import abstractmethod
from collections.abc import Sequence
from datetime import datetime

from app.domain.entities.activity import ActivityEntity
from app.domain.repositories.base_repository import BaseRepository
from app.domain.value_objects.core import ActivityId, TenantId


class ActivityRepository(BaseRepository[ActivityEntity, ActivityId]):
    """Repository interface for Activity aggregate."""

    @abstractmethod
    async def get_by_client_id(
        self, client_id: str, tenant_id: TenantId
    ) -> Sequence[ActivityEntity]:
        """Get all activities for a client."""

    @abstractmethod
    async def list_all(
        self,
        tenant_id: TenantId,
        client_id: str | None = None,
        activity_type: str | None = None,
        created_by: str | None = None,
        date_from: datetime | None = None,
        date_to: datetime | None = None,
        is_important: bool | None = None,
        search: str | None = None,
        limit: int = 100,
        offset: int = 0,
    ) -> Sequence[ActivityEntity]:
        """List activities with filtering."""

    @abstractmethod
    async def count(
        self,
        tenant_id: TenantId,
        client_id: str | None = None,
        activity_type: str | None = None,
        created_by: str | None = None,
        date_from: datetime | None = None,
        date_to: datetime | None = None,
        is_important: bool | None = None,
        search: str | None = None,
    ) -> int:
        """Count activities matching filters."""
