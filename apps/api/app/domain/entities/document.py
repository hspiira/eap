"""
Document Entity (Aggregate Root)

Represents a document with versioning support.
Documents can be files or URLs, and support versioning.
"""

from dataclasses import dataclass, field
from datetime import datetime

from app.domain.enums import DocumentStatus, DocumentType
from app.domain.events import (
    DocumentArchived,
    DocumentPublished,
    DocumentVersionCreated,
    DomainEvent,
)
from app.domain.exceptions import ConflictError, DomainError, InvariantViolation
from app.domain.value_objects.core import DocumentId, TenantId, UserId
from app.shared.utils.datetime import utc_now


@dataclass
class DocumentEntity:
    # Required fields
    id: DocumentId
    tenant_id: TenantId
    name: str
    document_type: DocumentType
    status: DocumentStatus
    version: int
    is_latest: bool
    created_at: datetime
    updated_at: datetime

    # Optional fields
    description: str | None = None
    file_path: str | None = None  # Path to uploaded file
    file_url: str | None = None  # External URL
    file_size: int | None = None  # Size in bytes
    mime_type: str | None = None
    previous_version_id: DocumentId | None = None  # Link to previous version
    uploaded_by: UserId | None = None
    client_id: str | None = None  # Associated client
    contract_id: str | None = None  # Associated contract
    person_id: str | None = None  # Associated person
    expires_at: datetime | None = None
    is_confidential: bool = False
    published_at: datetime | None = None
    archived_at: datetime | None = None
    deleted_at: datetime | None = None
    events: list[DomainEvent] = field(default_factory=list[DomainEvent])

    def __post_init__(self) -> None:
        """Validate invariants immediately after construction."""
        self._ensure_invariants()

    # === Behaviors ===

    def publish(self) -> None:
        """Publish document (make it available)."""
        if self.status == DocumentStatus.ARCHIVED:
            raise DomainError("Cannot publish archived document")
        if self.status == DocumentStatus.PUBLISHED:
            raise ConflictError("Document is already published")
        if self.deleted_at:
            raise DomainError("Cannot publish deleted document")

        self.status = DocumentStatus.PUBLISHED
        now = utc_now()
        self.published_at = now
        self.updated_at = now
        self.events.append(DocumentPublished(occurred_at=now, document_id=self.id))

    def archive(self) -> None:
        """Archive document."""
        if self.status == DocumentStatus.ARCHIVED:
            raise ConflictError("Document is already archived")
        if self.deleted_at:
            raise DomainError("Cannot archive deleted document")

        self.status = DocumentStatus.ARCHIVED
        now = utc_now()
        self.archived_at = now
        self.updated_at = now
        self.events.append(DocumentArchived(occurred_at=now, document_id=self.id))

    def create_new_version(
        self,
        new_version_id: DocumentId,
        name: str | None = None,
        description: str | None = None,
        file_path: str | None = None,
        file_url: str | None = None,
        file_size: int | None = None,
        mime_type: str | None = None,
    ) -> "DocumentEntity":
        """
        Create a new version of this document.

        Returns a new DocumentEntity with incremented version.
        The current document will be marked as not latest.
        """
        if self.deleted_at:
            raise DomainError("Cannot create version of deleted document")

        # Validate file or URL
        if not file_path and not file_url:
            raise DomainError("Either file_path or file_url must be provided")
        if file_path and file_url:
            raise DomainError("Cannot provide both file_path and file_url")

        # Mark current version as not latest
        self.is_latest = False
        self.updated_at = utc_now()

        # Create new version
        now = utc_now()
        new_version = DocumentEntity(
            id=new_version_id,
            tenant_id=self.tenant_id,
            name=name or self.name,
            document_type=self.document_type,
            status=DocumentStatus.DRAFT,
            version=self.version + 1,
            is_latest=True,
            description=description or self.description,
            file_path=file_path,
            file_url=file_url,
            file_size=file_size,
            mime_type=mime_type,
            previous_version_id=self.id,
            uploaded_by=self.uploaded_by,
            client_id=self.client_id,
            contract_id=self.contract_id,
            person_id=self.person_id,
            expires_at=self.expires_at,
            is_confidential=self.is_confidential,
            created_at=now,
            updated_at=now,
        )

        self.events.append(
            DocumentVersionCreated(
                occurred_at=now,
                document_id=self.id,
                new_version_id=new_version_id,
            )
        )

        return new_version

    def update_metadata(
        self,
        name: str | None = None,
        description: str | None = None,
    ) -> None:
        """Update document metadata."""
        if self.deleted_at:
            raise DomainError("Cannot update deleted document")
        if name:
            self.name = name
        if description is not None:
            self.description = description
        self.updated_at = utc_now()

    def set_confidentiality(self, is_confidential: bool) -> None:
        """Set document confidentiality."""
        if self.deleted_at:
            raise DomainError("Cannot update deleted document")
        self.is_confidential = is_confidential
        self.updated_at = utc_now()

    def set_expiry(self, expires_at: datetime | None) -> None:
        """Set document expiry date."""
        if self.deleted_at:
            raise DomainError("Cannot update deleted document")
        if expires_at and expires_at <= utc_now():
            raise DomainError("Expiry date must be in the future")
        self.expires_at = expires_at
        self.updated_at = utc_now()

    def check_expiry(self) -> bool:
        """Check if document has expired and update status if needed."""
        if self.expires_at and self.expires_at <= utc_now():
            if self.status != DocumentStatus.EXPIRED:
                self.status = DocumentStatus.EXPIRED
                self.updated_at = utc_now()
            return True
        return False

    def is_active(self) -> bool:
        """Check if document is active (published and not expired/deleted)."""
        if self.deleted_at:
            return False
        if self.status != DocumentStatus.PUBLISHED:
            return False
        if self.expires_at is None:
            return True
        return self.expires_at > utc_now()

    # === Invariants ===

    def _ensure_invariants(self) -> None:
        """Ensure document invariants are met."""
        if not self.name:
            raise InvariantViolation("Document must have a name")
        if not self.file_path and not self.file_url:
            raise InvariantViolation("Document must have either file_path or file_url")
        if self.file_path and self.file_url:
            raise InvariantViolation("Document cannot have both file_path and file_url")
        if self.version < 1:
            raise InvariantViolation("Document version must be at least 1")
        if self.expires_at and self.expires_at <= self.created_at:
            raise InvariantViolation("Expiry date must be after creation date")

    # === Public Properties ===

    def clear_events(self) -> None:
        self.events.clear()
