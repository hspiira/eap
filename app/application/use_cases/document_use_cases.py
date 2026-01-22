"""
Document Use Cases

Application services for Document aggregate operations.
"""

from datetime import datetime

from app.domain.entities.document import DocumentEntity
from app.domain.enums import DocumentStatus, DocumentType
from app.domain.repositories.document_repository import DocumentRepository
from app.domain.value_objects.core import DocumentId, TenantId, UserId
from app.shared.utils.datetime import utc_now


class CreateDocumentUseCase:
    """Use case for creating a new document."""

    def __init__(self, document_repository: DocumentRepository):
        self.document_repository = document_repository

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
        """
        Create a new document.

        Args:
            document_id: Unique document identifier
            tenant_id: Tenant identifier
            name: Document name
            document_type: Document type
            file_path: Path to uploaded file (optional)
            file_url: External URL to document (optional)
            file_size: File size in bytes (optional)
            mime_type: MIME type (optional)
            description: Document description (optional)
            uploaded_by: User who uploaded the document (optional)
            client_id: Associated client ID (optional)
            contract_id: Associated contract ID (optional)
            person_id: Associated person ID (optional)
            expires_at: Expiry date (optional)
            is_confidential: Whether document is confidential

        Returns:
            Created DocumentEntity

        Raises:
            ValueError: If validation fails
        """
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
            _id=document_id,
            _tenant_id=tenant_id,
            _name=name,
            _document_type=document_type,
            _status=DocumentStatus.DRAFT,
            _version=1,
            _is_latest=True,
            _description=description,
            _file_path=file_path,
            _file_url=file_url,
            _file_size=file_size,
            _mime_type=mime_type,
            _uploaded_by=uploaded_by,
            _client_id=client_id,
            _contract_id=contract_id,
            _person_id=person_id,
            _expires_at=expires_at,
            _is_confidential=is_confidential,
            _created_at=utc_now(),
            _updated_at=utc_now(),
        )

        # Save document
        await self.document_repository.save(document)

        return document


class PublishDocumentUseCase:
    """Use case for publishing a document."""

    def __init__(self, document_repository: DocumentRepository):
        self.document_repository = document_repository

    async def execute(self, document_id: DocumentId) -> DocumentEntity:
        """
        Publish a document.

        Args:
            document_id: Document identifier

        Returns:
            Published DocumentEntity

        Raises:
            ValueError: If document not found
            DomainError: If publish is invalid
        """
        document = await self.document_repository.get_by_id(document_id)
        if not document:
            raise ValueError(f"Document {document_id.value} not found")

        document.publish()
        await self.document_repository.save(document)

        return document


class ArchiveDocumentUseCase:
    """Use case for archiving a document."""

    def __init__(self, document_repository: DocumentRepository):
        self.document_repository = document_repository

    async def execute(self, document_id: DocumentId) -> DocumentEntity:
        """
        Archive a document.

        Args:
            document_id: Document identifier

        Returns:
            Archived DocumentEntity

        Raises:
            ValueError: If document not found
            DomainError: If archive is invalid
        """
        document = await self.document_repository.get_by_id(document_id)
        if not document:
            raise ValueError(f"Document {document_id.value} not found")

        document.archive()
        await self.document_repository.save(document)

        return document


class CreateDocumentVersionUseCase:
    """Use case for creating a new document version."""

    def __init__(self, document_repository: DocumentRepository):
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
        """
        Create a new version of a document.

        Args:
            document_id: Original document identifier
            new_version_id: New version identifier
            name: Document name (optional, uses original if not provided)
            description: Document description (optional)
            file_path: Path to uploaded file (optional)
            file_url: External URL to document (optional)
            file_size: File size in bytes (optional)
            mime_type: MIME type (optional)

        Returns:
            New DocumentEntity version

        Raises:
            ValueError: If document not found or validation fails
            DomainError: If version creation is invalid
        """
        # Get latest version
        document = await self.document_repository.get_by_id(document_id)
        if not document:
            raise ValueError(f"Document {document_id.value} not found")

        # Get the actual latest version
        latest = await self.document_repository.get_latest_version(
            document_id, document._tenant_id
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
        await self.document_repository.save(document)  # Update old version (is_latest=False)
        await self.document_repository.save(new_version)  # Save new version

        return new_version


class UpdateDocumentMetadataUseCase:
    """Use case for updating document metadata."""

    def __init__(self, document_repository: DocumentRepository):
        self.document_repository = document_repository

    async def execute(
        self,
        document_id: DocumentId,
        name: str | None = None,
        description: str | None = None,
    ) -> DocumentEntity:
        """
        Update document metadata.

        Args:
            document_id: Document identifier
            name: Document name (optional)
            description: Document description (optional)

        Returns:
            Updated DocumentEntity

        Raises:
            ValueError: If document not found
            DomainError: If update is invalid
        """
        document = await self.document_repository.get_by_id(document_id)
        if not document:
            raise ValueError(f"Document {document_id.value} not found")

        document.update_metadata(name=name, description=description)
        await self.document_repository.save(document)

        return document


class SetDocumentConfidentialityUseCase:
    """Use case for setting document confidentiality."""

    def __init__(self, document_repository: DocumentRepository):
        self.document_repository = document_repository

    async def execute(
        self, document_id: DocumentId, is_confidential: bool
    ) -> DocumentEntity:
        """
        Set document confidentiality.

        Args:
            document_id: Document identifier
            is_confidential: Whether document is confidential

        Returns:
            Updated DocumentEntity

        Raises:
            ValueError: If document not found
            DomainError: If update is invalid
        """
        document = await self.document_repository.get_by_id(document_id)
        if not document:
            raise ValueError(f"Document {document_id.value} not found")

        document.set_confidentiality(is_confidential)
        await self.document_repository.save(document)

        return document


class SetDocumentExpiryUseCase:
    """Use case for setting document expiry."""

    def __init__(self, document_repository: DocumentRepository):
        self.document_repository = document_repository

    async def execute(
        self, document_id: DocumentId, expires_at: datetime | None
    ) -> DocumentEntity:
        """
        Set document expiry date.

        Args:
            document_id: Document identifier
            expires_at: Expiry date (None to remove expiry)

        Returns:
            Updated DocumentEntity

        Raises:
            ValueError: If document not found
            DomainError: If update is invalid
        """
        document = await self.document_repository.get_by_id(document_id)
        if not document:
            raise ValueError(f"Document {document_id.value} not found")

        document.set_expiry(expires_at)
        await self.document_repository.save(document)

        return document


class GetDocumentUseCase:
    """Use case for retrieving a document."""

    def __init__(self, document_repository: DocumentRepository):
        self.document_repository = document_repository

    async def execute(self, document_id: DocumentId) -> DocumentEntity | None:
        """
        Get document by ID.

        Args:
            document_id: Document identifier

        Returns:
            DocumentEntity if found, None otherwise
        """
        return await self.document_repository.get_by_id(document_id)
