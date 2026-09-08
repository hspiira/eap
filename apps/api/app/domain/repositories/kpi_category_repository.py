"""KPI category repository port.

The taxonomy is global and curated centrally; writes are platform-admin only.
"""

from abc import ABC, abstractmethod

from app.domain.entities.kpi_category import KPICategory


class KPICategoryRepository(ABC):
    @abstractmethod
    async def list_all(self, *, active_only: bool = True) -> list[KPICategory]: ...

    @abstractmethod
    async def get_by_code(self, code: str) -> KPICategory | None: ...

    @abstractmethod
    async def get_by_id(self, category_id: str) -> KPICategory | None: ...

    @abstractmethod
    async def create(
        self, *, code: str, name: str, description: str | None, sort_order: int
    ) -> KPICategory: ...

    @abstractmethod
    async def update(
        self,
        category_id: str,
        *,
        name: str | None = None,
        description: str | None = None,
        sort_order: int | None = None,
    ) -> KPICategory | None: ...

    @abstractmethod
    async def set_active(self, category_id: str, *, is_active: bool) -> KPICategory | None: ...
