"""Presenting problem repository port.

The taxonomy is global and curated centrally; writes are platform-admin only.
"""

from abc import ABC, abstractmethod

from app.domain.entities.presenting_problem import PresentingProblem


class PresentingProblemRepository(ABC):
    @abstractmethod
    async def list_all(self, *, active_only: bool = True) -> list[PresentingProblem]: ...

    @abstractmethod
    async def get_by_code(self, code: str) -> PresentingProblem | None: ...

    @abstractmethod
    async def get_by_id(self, problem_id: str) -> PresentingProblem | None: ...

    @abstractmethod
    async def create(
        self, *, code: str, name: str, description: str | None, sort_order: int
    ) -> PresentingProblem: ...

    @abstractmethod
    async def update(
        self,
        problem_id: str,
        *,
        name: str | None = None,
        description: str | None = None,
        sort_order: int | None = None,
    ) -> PresentingProblem | None: ...

    @abstractmethod
    async def set_active(self, problem_id: str, *, is_active: bool) -> PresentingProblem | None: ...
