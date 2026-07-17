"""
Document Use Cases

Application services for Document aggregate operations.
Refactored to use base use case classes.
"""

from datetime import datetime

from app.application.use_cases.base import BaseUseCase
from app.domain.entities.document import DocumentEntity
from app.domain.enums import DocumentStatus, DocumentType
from app.domain.repositories.document_repository import DocumentRepository
from app.domain.value_objects.core import DocumentId, TenantId, UserId
from app.shared.utils.datetime import utc_now

# Lifecycle (archive/publish) dispatched via TransitionUseCase + DocumentTransition.


class CreateDocumentUseCase(BaseUseCase[DocumentEntity, DocumentId]):
    """Use case for creating a new document."""

    def __init__(self, document_repository: DocumentRepository):
        super().__init__(document_repository)

    async def execute(
        self,
        document_id: DocumentId,
        tenant_id: TenantId,
        name: str,
        document_type: DocumentType,
        file_path: str | None = None,
        file_url: str | None = None,
        file_size: int | None = None,
        mime_type: str | None = None,
        description: str | None = None,
        uploaded_by: UserId | None = None,
        client_id: str | None = None,
        contract_id: str | None = None,
        person_id: str | None = None,
        expires_at: datetime | None = None,
        is_confidential: bool = False,
    ) -> DocumentEntity:
        """Create a new document."""
        # Validate file or URL
        if not file_path and not file_url:
            raise ValueError("Either file_path or file_url must be provided")
        if file_path and file_url:
            raise ValueError("Cannot provide both file_path and file_url")

        # Validate expiry date
        if expires_at and expires_at <= utc_now():
            raise ValueError("Expiry date must be in the future")

        # Create document entity
        document = DocumentEntity(
            id=document_id,
            tenant_id=tenant_id,
            name=name,
            document_type=document_type,
            status=DocumentStatus.DRAFT,
            version=1,
            is_latest=True,
            description=description,
            file_path=file_path,
            file_url=file_url,
            file_size=file_size,
            mime_type=mime_type,
            uploaded_by=uploaded_by,
            client_id=client_id,
            contract_id=contract_id,
            person_id=person_id,
            expires_at=expires_at,
            is_confidential=is_confidential,
            created_at=utc_now(),
            updated_at=utc_now(),
        )

        return await self._save_and_publish_events(document)


# =============================================================================
# SPECIALIZED COMMAND USE CASES
# =============================================================================


class CreateDocumentVersionUseCase(BaseUseCase[DocumentEntity, DocumentId]):
    """Use case for creating a new document version."""

    def __init__(self, document_repository: DocumentRepository):
        super().__init__(document_repository)
        self.document_repository = document_repository

    async def execute(
        self,
        document_id: DocumentId,
        new_version_id: DocumentId,
        name: str | None = None,
        description: str | None = None,
        file_path: str | None = None,
        file_url: str | None = None,
        file_size: int | None = None,
        mime_type: str | None = None,
    ) -> DocumentEntity:
        """Create a new version of a document."""
        # Get latest version
        document = await self._get_entity_or_raise(document_id, "Document")

        # Get the actual latest version
        latest = await self.document_repository.get_latest_version(
            document_id, document.tenant_id
        )
        if latest:
            document = latest

        # Create new version
        new_version = document.create_new_version(
            new_version_id=new_version_id,
            name=name,
            description=description,
            file_path=file_path,
            file_url=file_url,
            file_size=file_size,
            mime_type=mime_type,
        )

        # Save both old and new versions
        await self.repository.save(document)  # Update old version (is_latest=False)
        await self.repository.save(new_version)  # Save new version

        return new_version


# =============================================================================
# UPDATE USE CASES
# =============================================================================


class UpdateDocumentMetadataUseCase(BaseUseCase[DocumentEntity, DocumentId]):
    """Use case for updating document metadata."""

    def __init__(self, document_repository: DocumentRepository):
        super().__init__(document_repository)

    async def execute(
        self,
        document_id: DocumentId,
        name: str | None = None,
        description: str | None = None,
    ) -> DocumentEntity:
        """Update document metadata."""
        document = await self._get_entity_or_raise(document_id, "Document")
        document.update_metadata(name=name, description=description)
        return await self._save_and_publish_events(document)


class SetDocumentConfidentialityUseCase(BaseUseCase[DocumentEntity, DocumentId]):
    """Use case for setting document confidentiality."""

    def __init__(self, document_repository: DocumentRepository):
        super().__init__(document_repository)

    async def execute(
        self, document_id: DocumentId, is_confidential: bool
    ) -> DocumentEntity:
        """Set document confidentiality."""
        document = await self._get_entity_or_raise(document_id, "Document")
        document.set_confidentiality(is_confidential)
        return await self._save_and_publish_events(document)


class SetDocumentExpiryUseCase(BaseUseCase[DocumentEntity, DocumentId]):
    """Use case for setting document expiry."""

    def __init__(self, document_repository: DocumentRepository):
        super().__init__(document_repository)

    async def execute(
        self, document_id: DocumentId, expires_at: datetime | None
    ) -> DocumentEntity:
        """Set document expiry date."""
        document = await self._get_entity_or_raise(document_id, "Document")
        document.set_expiry(expires_at)
        return await self._save_and_publish_events(document)


# =============================================================================
# QUERY USE CASE
# =============================================================================


class GetDocumentUseCase(BaseUseCase[DocumentEntity, DocumentId]):
    """Use case for retrieving a document."""

    def __init__(self, document_repository: DocumentRepository):
        super().__init__(document_repository)

    async def execute(self, document_id: DocumentId) -> DocumentEntity | None:
        """Get document by ID."""
        return await self.repository.get_by_id(document_id)
