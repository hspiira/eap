"""Client tier repository port.

The taxonomy is global and curated centrally; writes are platform-admin only.
"""

from abc import ABC, abstractmethod

from app.domain.entities.client_tier import ClientTier


class ClientTierRepository(ABC):
    @abstractmethod
    async def list_all(self, *, active_only: bool = True) -> list[ClientTier]: ...

    @abstractmethod
    async def get_by_code(self, code: str) -> ClientTier | None: ...

    @abstractmethod
    async def get_by_id(self, tier_id: str) -> ClientTier | None: ...

    @abstractmethod
    async def create(
        self, *, code: str, name: str, description: str | None, sort_order: int
    ) -> ClientTier: ...

    @abstractmethod
    async def update(
        self,
        tier_id: str,
        *,
        name: str | None = None,
        description: str | None = None,
        sort_order: int | None = None,
    ) -> ClientTier | None: ...

    @abstractmethod
    async def set_active(self, tier_id: str, *, is_active: bool) -> ClientTier | None: ...
