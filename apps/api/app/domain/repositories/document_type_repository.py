"""Document type repository port.

The taxonomy is global and curated centrally; writes are platform-admin only.
"""

from abc import ABC, abstractmethod

from app.domain.entities.document_type import DocumentType


class DocumentTypeRepository(ABC):
    @abstractmethod
    async def list_all(self, *, active_only: bool = True) -> list[DocumentType]: ...

    @abstractmethod
    async def get_by_code(self, code: str) -> DocumentType | None: ...

    @abstractmethod
    async def get_by_id(self, type_id: str) -> DocumentType | None: ...

    @abstractmethod
    async def create(
        self, *, code: str, name: str, description: str | None, sort_order: int
    ) -> DocumentType: ...

    @abstractmethod
    async def update(
        self,
        type_id: str,
        *,
        name: str | None = None,
        description: str | None = None,
        sort_order: int | None = None,
    ) -> DocumentType | None: ...

    @abstractmethod
    async def set_active(self, type_id: str, *, is_active: bool) -> DocumentType | None: ...
