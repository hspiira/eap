"""Provider repository port.

Providers have no domain entity yet, so this port still traffics in ORM rows
rather than aggregates. The `Any` annotations state that plainly instead of
leaving the shape unknown; give it a real entity and the signatures tighten.
"""

from abc import abstractmethod
from typing import Any

from app.domain.value_objects.core import ProviderId, TenantId


class ProviderRepository:
    @abstractmethod
    async def get_by_id(self, provider_id: ProviderId) -> Any: ...

    @abstractmethod
    async def list_for_tenant(
        self, tenant_id: TenantId, *, limit: int = 100, offset: int = 0
    ) -> list[Any]: ...

    @abstractmethod
    async def count(self, tenant_id: TenantId) -> int: ...

    @abstractmethod
    async def save(self, provider: Any) -> None: ...

    @abstractmethod
    async def get_user_in_tenant(self, user_id: str, tenant_id: TenantId) -> Any: ...

    @abstractmethod
    async def create(
        self,
        *,
        tenant_id: TenantId,
        user_id: str,
        provider_profile: dict[str, Any],
        license_info: Any,
    ) -> Any: ...
