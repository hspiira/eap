"""Domain events for the document bounded context."""

from dataclasses import dataclass

from app.domain.events.base import DomainEvent
from app.domain.value_objects.core import DocumentId


@dataclass(frozen=True)
class DocumentPublished(DomainEvent):
    """Event raised when a document is published."""

    document_id: DocumentId


@dataclass(frozen=True)
class DocumentArchived(DomainEvent):
    """Event raised when a document is archived."""

    document_id: DocumentId


@dataclass(frozen=True)
class DocumentVersionCreated(DomainEvent):
    """Event raised when a new document version is created."""

    document_id: DocumentId
    new_version_id: DocumentId
