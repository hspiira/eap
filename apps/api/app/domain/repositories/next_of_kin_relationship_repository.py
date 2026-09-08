"""Next-of-kin relationship repository port.

The taxonomy is global and curated centrally; writes are platform-admin only.
"""

from abc import ABC, abstractmethod

from app.domain.entities.next_of_kin_relationship import NextOfKinRelationship


class NextOfKinRelationshipRepository(ABC):
    @abstractmethod
    async def list_all(self, *, active_only: bool = True) -> list[NextOfKinRelationship]: ...

    @abstractmethod
    async def get_by_code(self, code: str) -> NextOfKinRelationship | None: ...

    @abstractmethod
    async def get_by_id(self, relationship_id: str) -> NextOfKinRelationship | None: ...

    @abstractmethod
    async def create(
        self, *, code: str, name: str, description: str | None, sort_order: int
    ) -> NextOfKinRelationship: ...

    @abstractmethod
    async def update(
        self,
        relationship_id: str,
        *,
        name: str | None = None,
        description: str | None = None,
        sort_order: int | None = None,
    ) -> NextOfKinRelationship | None: ...

    @abstractmethod
    async def set_active(
        self, relationship_id: str, *, is_active: bool
    ) -> NextOfKinRelationship | None: ...
