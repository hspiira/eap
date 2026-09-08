"""
Document Repository Interface

Defines the contract for Document data access.
Implementation lives in infrastructure layer.
"""

from abc import abstractmethod
from collections.abc import Sequence

from app.domain.entities.document import DocumentEntity
from app.domain.enums import DocumentStatus
from app.domain.repositories.base_repository import BaseRepository
from app.domain.value_objects.core import DocumentId, TenantId


class DocumentRepository(BaseRepository[DocumentEntity, DocumentId]):
    """
    Repository interface for Document aggregate.

    Repositories are ONLY for aggregate roots.
    This interface is in the domain layer - implementation in infrastructure.
    """

    @abstractmethod
    async def get_versions(
        self, document_id: DocumentId, tenant_id: TenantId
    ) -> Sequence[DocumentEntity]:
        """
        Get all versions of a document (by original document ID).

        Args:
            document_id: Original document identifier
            tenant_id: Tenant identifier

        Returns:
            Sequence of DocumentEntity versions
        """

    @abstractmethod
    async def get_latest_version(
        self, document_id: DocumentId, tenant_id: TenantId
    ) -> DocumentEntity | None:
        """
        Get the latest version of a document.

        Args:
            document_id: Original document identifier
            tenant_id: Tenant identifier

        Returns:
            Latest DocumentEntity if found, None otherwise
        """

    @abstractmethod
    async def list_all(
        self,
        tenant_id: TenantId,
        document_type: str | None = None,
        status: DocumentStatus | None = None,
        client_id: str | None = None,
        contract_id: str | None = None,
        person_id: str | None = None,
        is_confidential: bool | None = None,
        search: str | None = None,
        limit: int = 100,
        offset: int = 0,
        sort_by: str = "created_at",
        sort_desc: bool = True,
    ) -> Sequence[DocumentEntity]:
        """
        List documents with filtering, searching, and pagination.

        Args:
            tenant_id: Tenant identifier
            document_type: Filter by document type
            status: Filter by document status
            client_id: Filter by associated client
            contract_id: Filter by associated contract
            person_id: Filter by associated person
            is_confidential: Filter by confidentiality
            search: Search in document name or description
            limit: Maximum number of results
            offset: Number of results to skip
            sort_by: Field to sort by
            sort_desc: Sort in descending order

        Returns:
            Sequence of DocumentEntity (only latest versions)
        """

    @abstractmethod
    async def count(
        self,
        tenant_id: TenantId,
        document_type: str | None = None,
        status: DocumentStatus | None = None,
        client_id: str | None = None,
        contract_id: str | None = None,
        person_id: str | None = None,
        is_confidential: bool | None = None,
        search: str | None = None,
    ) -> int:
        """
        Count documents matching filters.

        Args:
            tenant_id: Tenant identifier
            document_type: Filter by document type
            status: Filter by document status
            client_id: Filter by associated client
            contract_id: Filter by associated contract
            person_id: Filter by associated person
            is_confidential: Filter by confidentiality
            search: Search in document name or description

        Returns:
            Total count (only latest versions)
        """
