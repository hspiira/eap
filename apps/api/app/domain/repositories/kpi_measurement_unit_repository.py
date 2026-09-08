"""KPI measurement unit repository port.

The taxonomy is global and curated centrally; writes are platform-admin only.
"""

from abc import ABC, abstractmethod

from app.domain.entities.kpi_measurement_unit import KPIMeasurementUnit


class KPIMeasurementUnitRepository(ABC):
    @abstractmethod
    async def list_all(self, *, active_only: bool = True) -> list[KPIMeasurementUnit]: ...

    @abstractmethod
    async def get_by_code(self, code: str) -> KPIMeasurementUnit | None: ...

    @abstractmethod
    async def get_by_id(self, unit_id: str) -> KPIMeasurementUnit | None: ...

    @abstractmethod
    async def create(
        self, *, code: str, name: str, description: str | None, sort_order: int
    ) -> KPIMeasurementUnit: ...

    @abstractmethod
    async def update(
        self,
        unit_id: str,
        *,
        name: str | None = None,
        description: str | None = None,
        sort_order: int | None = None,
    ) -> KPIMeasurementUnit | None: ...

    @abstractmethod
    async def set_active(self, unit_id: str, *, is_active: bool) -> KPIMeasurementUnit | None: ...
