"""
Document Entity (Aggregate Root)

Represents a document with versioning support.
Documents can be files or URLs, and support versioning.
"""

from dataclasses import dataclass, field
from datetime import datetime

from app.domain.enums import DocumentStatus, DocumentType
from app.domain.events import DomainEvent, DocumentPublished, DocumentArchived, DocumentVersionCreated
from app.domain.exceptions import DomainError, InvariantViolation
from app.domain.value_objects.core import DocumentId, TenantId, UserId
from app.shared.utils.datetime import utc_now


@dataclass
class DocumentEntity:
    # Required fields
    _id: DocumentId
    _tenant_id: TenantId
    _name: str
    _document_type: DocumentType
    _status: DocumentStatus
    _version: int
    _is_latest: bool
    _created_at: datetime
    _updated_at: datetime
    
    # Optional fields
    _description: str | None = None
    _file_path: str | None = None  # Path to uploaded file
    _file_url: str | None = None  # External URL
    _file_size: int | None = None  # Size in bytes
    _mime_type: str | None = None
    _previous_version_id: DocumentId | None = None  # Link to previous version
    _uploaded_by: UserId | None = None
    _client_id: str | None = None  # Associated client
    _contract_id: str | None = None  # Associated contract
    _person_id: str | None = None  # Associated person
    _expires_at: datetime | None = None
    _is_confidential: bool = False
    _published_at: datetime | None = None
    _archived_at: datetime | None = None
    _deleted_at: datetime | None = None
    _events: list[DomainEvent] = field(default_factory=list)
    
    def __post_init__(self) -> None:
        """Validate invariants immediately after construction."""
        self._ensure_invariants()
    
    # === Behaviors ===
    
    def publish(self) -> None:
        """Publish document (make it available)."""
        if self._status == DocumentStatus.ARCHIVED:
            raise DomainError("Cannot publish archived document")
        if self._status == DocumentStatus.PUBLISHED:
            raise DomainError("Document is already published")
        if self._deleted_at:
            raise DomainError("Cannot publish deleted document")
        
        self._status = DocumentStatus.PUBLISHED
        now = utc_now()
        self._published_at = now
        self._updated_at = now
        self._events.append(DocumentPublished(occurred_at=now, document_id=self._id))
    
    def archive(self) -> None:
        """Archive document."""
        if self._status == DocumentStatus.ARCHIVED:
            raise DomainError("Document is already archived")
        if self._deleted_at:
            raise DomainError("Cannot archive deleted document")
        
        self._status = DocumentStatus.ARCHIVED
        now = utc_now()
        self._archived_at = now
        self._updated_at = now
        self._events.append(DocumentArchived(occurred_at=now, document_id=self._id))
    
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
        if self._deleted_at:
            raise DomainError("Cannot create version of deleted document")
        
        # Validate file or URL
        if not file_path and not file_url:
            raise DomainError("Either file_path or file_url must be provided")
        if file_path and file_url:
            raise DomainError("Cannot provide both file_path and file_url")
        
        # Mark current version as not latest
        self._is_latest = False
        self._updated_at = utc_now()
        
        # Create new version
        new_version = DocumentEntity(
            _id=new_version_id,
            _tenant_id=self._tenant_id,
            _name=name or self._name,
            _document_type=self._document_type,
            _status=DocumentStatus.DRAFT,
            _version=self._version + 1,
            _is_latest=True,
            _description=description or self._description,
            _file_path=file_path,
            _file_url=file_url,
            _file_size=file_size,
            _mime_type=mime_type,
            _previous_version_id=self._id,
            _uploaded_by=self._uploaded_by,
            _client_id=self._client_id,
            _contract_id=self._contract_id,
            _person_id=self._person_id,
            _expires_at=self._expires_at,
            _is_confidential=self._is_confidential,
            _created_at=utc_now(),
            _updated_at=utc_now(),
        )
        
        now = utc_now()
        self._events.append(
            DocumentVersionCreated(
                occurred_at=now,
                document_id=self._id,
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
        if self._deleted_at:
            raise DomainError("Cannot update deleted document")
        if name:
            self._name = name
        if description is not None:
            self._description = description
        self._updated_at = utc_now()
    
    def set_confidentiality(self, is_confidential: bool) -> None:
        """Set document confidentiality."""
        if self._deleted_at:
            raise DomainError("Cannot update deleted document")
        self._is_confidential = is_confidential
        self._updated_at = utc_now()
    
    def set_expiry(self, expires_at: datetime | None) -> None:
        """Set document expiry date."""
        if self._deleted_at:
            raise DomainError("Cannot update deleted document")
        if expires_at and expires_at <= utc_now():
            raise DomainError("Expiry date must be in the future")
        self._expires_at = expires_at
        self._updated_at = utc_now()
    
    def check_expiry(self) -> bool:
        """Check if document has expired and update status if needed."""
        if self._expires_at and self._expires_at <= utc_now():
            if self._status != DocumentStatus.EXPIRED:
                self._status = DocumentStatus.EXPIRED
                self._updated_at = utc_now()
            return True
        return False
    
    def is_active(self) -> bool:
        """Check if document is active (published and not expired/deleted)."""
        if self._deleted_at:
            return False
        self.check_expiry()  # Update status if expired
        return self._status == DocumentStatus.PUBLISHED and not self._expires_at or self._expires_at > utc_now()
    
    # === Invariants ===
    
    def _ensure_invariants(self) -> None:
        """Ensure document invariants are met."""
        if not self._name:
            raise InvariantViolation("Document must have a name")
        if not self._file_path and not self._file_url:
            raise InvariantViolation("Document must have either file_path or file_url")
        if self._file_path and self._file_url:
            raise InvariantViolation("Document cannot have both file_path and file_url")
        if self._version < 1:
            raise InvariantViolation("Document version must be at least 1")
        if self._expires_at and self._expires_at <= self._created_at:
            raise InvariantViolation("Expiry date must be after creation date")
