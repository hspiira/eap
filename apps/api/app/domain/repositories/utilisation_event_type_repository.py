"""Utilisation event type repository port.

The taxonomy is global and curated centrally; writes are platform-admin only.
"""

from abc import ABC, abstractmethod

from app.domain.entities.utilisation_event_type import UtilisationEventType


class UtilisationEventTypeRepository(ABC):
    @abstractmethod
    async def list_all(self, *, active_only: bool = True) -> list[UtilisationEventType]: ...

    @abstractmethod
    async def get_by_code(self, code: str) -> UtilisationEventType | None: ...

    @abstractmethod
    async def get_by_id(self, event_type_id: str) -> UtilisationEventType | None: ...

    @abstractmethod
    async def create(
        self, *, code: str, name: str, description: str | None, sort_order: int
    ) -> UtilisationEventType: ...

    @abstractmethod
    async def update(
        self,
        event_type_id: str,
        *,
        name: str | None = None,
        description: str | None = None,
        sort_order: int | None = None,
    ) -> UtilisationEventType | None: ...

    @abstractmethod
    async def set_active(
        self, event_type_id: str, *, is_active: bool
    ) -> UtilisationEventType | None: ...
