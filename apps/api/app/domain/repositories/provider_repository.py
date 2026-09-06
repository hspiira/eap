"""Provider repository port."""

from abc import abstractmethod

from app.domain.value_objects.core import ProviderId, TenantId


class ProviderRepository:
    @abstractmethod
    async def get_by_id(self, provider_id: ProviderId): ...

    @abstractmethod
    async def list_for_tenant(self, tenant_id: TenantId, *, limit: int = 100, offset: int = 0): ...

    @abstractmethod
    async def count(self, tenant_id: TenantId) -> int: ...

    @abstractmethod
    async def save(self, provider): ...
