"""Engagement repository port (Phase 4 #D-Engagement)."""

from app.domain.entities.engagement import Engagement
from app.domain.enums import EngagementStatus
from app.domain.repositories.base_repository import BaseRepository
from app.domain.value_objects.core import ClientId, EngagementId, TenantId


class EngagementRepository(BaseRepository[Engagement, EngagementId]):
    async def list_for_tenant(
        self, tenant_id: TenantId, *, limit: int = 50, offset: int = 0
    ) -> list[Engagement]: ...

    async def list_all(
        self,
        tenant_id: TenantId,
        *,
        client_id: ClientId | None = None,
        status: EngagementStatus | None = None,
        search: str | None = None,
        limit: int = 100,
        offset: int = 0,
    ) -> list[Engagement]: ...

    async def count(
        self,
        tenant_id: TenantId,
        *,
        client_id: ClientId | None = None,
        status: EngagementStatus | None = None,
        search: str | None = None,
    ) -> int: ...

    async def list_for_client(
        self,
        tenant_id: TenantId,
        client_id: ClientId,
        *,
        limit: int = 100,
    ) -> list[Engagement]: ...
