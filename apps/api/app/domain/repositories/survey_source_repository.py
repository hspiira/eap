"""Survey source repository port.

The taxonomy is global and curated centrally; writes are platform-admin only.
"""

from abc import ABC, abstractmethod

from app.domain.entities.survey_source import SurveySource


class SurveySourceRepository(ABC):
    @abstractmethod
    async def list_all(self, *, active_only: bool = True) -> list[SurveySource]: ...

    @abstractmethod
    async def get_by_code(self, code: str) -> SurveySource | None: ...

    @abstractmethod
    async def get_by_id(self, source_id: str) -> SurveySource | None: ...

    @abstractmethod
    async def create(
        self, *, code: str, name: str, description: str | None, sort_order: int
    ) -> SurveySource: ...

    @abstractmethod
    async def update(
        self,
        source_id: str,
        *,
        name: str | None = None,
        description: str | None = None,
        sort_order: int | None = None,
    ) -> SurveySource | None: ...

    @abstractmethod
    async def set_active(self, source_id: str, *, is_active: bool) -> SurveySource | None: ...
