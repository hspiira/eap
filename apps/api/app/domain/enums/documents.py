from enum import Enum


class DocumentStatus(str, Enum):
    """Status of a document."""

    DRAFT = "Draft"
    PUBLISHED = "Published"
    ARCHIVED = "Archived"
    EXPIRED = "Expired"
