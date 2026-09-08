"""Service category repository port.

The taxonomy is global and curated centrally; writes are platform-admin only.
"""

from abc import ABC, abstractmethod

from app.domain.entities.service_category import ServiceCategory


class ServiceCategoryRepository(ABC):
    @abstractmethod
    async def list_all(self, *, active_only: bool = True) -> list[ServiceCategory]: ...

    @abstractmethod
    async def get_by_code(self, code: str) -> ServiceCategory | None: ...

    @abstractmethod
    async def get_by_id(self, category_id: str) -> ServiceCategory | None: ...

    @abstractmethod
    async def create(
        self, *, code: str, name: str, description: str | None, sort_order: int
    ) -> ServiceCategory: ...

    @abstractmethod
    async def update(
        self,
        category_id: str,
        *,
        name: str | None = None,
        description: str | None = None,
        sort_order: int | None = None,
    ) -> ServiceCategory | None: ...

    @abstractmethod
    async def set_active(self, category_id: str, *, is_active: bool) -> ServiceCategory | None: ...
