"""
Document API Schemas (DTOs)

Pydantic models for request/response validation.
Separate from domain entities.
"""

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from app.domain.enums import DocumentStatus, DocumentType
from app.shared.utils.document_validation import (
    validate_document_file_path,
    validate_document_file_url,
)


def _get_document_storage_path() -> str:
    from app.core.config import settings
    return getattr(settings, "DOCUMENT_STORAGE_PATH", "./uploads")


def _get_allowed_url_schemes() -> list[str]:
    from app.core.config import settings
    raw = getattr(settings, "DOCUMENT_ALLOWED_URL_SCHEMES", "https")
    return [s.strip().lower() for s in raw.split(",") if s.strip()]


# === Request Schemas ===

class DocumentCreate(BaseModel):
    """Request schema for creating a document."""

    name: str = Field(..., min_length=1, max_length=255, description="Document name")
    description: str | None = Field(None, description="Document description")
    document_type: DocumentType = Field(..., description="Document type")
    file_path: str | None = Field(None, max_length=500, description="Path to uploaded file")
    file_url: str | None = Field(None, max_length=500, description="External URL to document")
    file_size: int | None = Field(None, ge=0, description="File size in bytes")
    mime_type: str | None = Field(None, max_length=100, description="MIME type")
    client_id: str | None = Field(None, description="Associated client ID")
    contract_id: str | None = Field(None, description="Associated contract ID")
    person_id: str | None = Field(None, description="Associated person ID")
    expires_at: datetime | None = Field(None, description="Expiry date")
    is_confidential: bool = Field(False, description="Whether document is confidential")

    model_config = ConfigDict(extra="forbid")

    @field_validator("file_path")
    @classmethod
    def validate_file_path(cls, v: str | None) -> str | None:
        if not v:
            return v
        return validate_document_file_path(v, _get_document_storage_path())

    @field_validator("file_url")
    @classmethod
    def validate_file_url(cls, v: str | None) -> str | None:
        if not v:
            return v
        return validate_document_file_url(v, _get_allowed_url_schemes())

    @model_validator(mode="after")
    def require_path_or_url(self):
        if not self.file_path and not self.file_url:
            raise ValueError("Either file_path or file_url must be provided")
        if self.file_path and self.file_url:
            raise ValueError("Cannot provide both file_path and file_url")
        return self


class DocumentCreateVersion(BaseModel):
    """Request schema for creating a new document version."""

    name: str | None = Field(None, min_length=1, max_length=255, description="Document name")
    description: str | None = Field(None, description="Document description")
    file_path: str | None = Field(None, max_length=500, description="Path to uploaded file")
    file_url: str | None = Field(None, max_length=500, description="External URL to document")
    file_size: int | None = Field(None, ge=0, description="File size in bytes")
    mime_type: str | None = Field(None, max_length=100, description="MIME type")

    model_config = ConfigDict(extra="forbid")

    @field_validator("file_path")
    @classmethod
    def validate_file_path(cls, v: str | None) -> str | None:
        if not v:
            return v
        return validate_document_file_path(v, _get_document_storage_path())

    @field_validator("file_url")
    @classmethod
    def validate_file_url(cls, v: str | None) -> str | None:
        if not v:
            return v
        return validate_document_file_url(v, _get_allowed_url_schemes())

    @model_validator(mode="after")
    def require_path_or_url(self):
        if not self.file_path and not self.file_url:
            raise ValueError("Either file_path or file_url must be provided")
        if self.file_path and self.file_url:
            raise ValueError("Cannot provide both file_path and file_url")
        return self


class DocumentUpdate(BaseModel):
    """Request schema for updating document metadata."""

    name: str | None = Field(None, min_length=1, max_length=255, description="Document name")
    description: str | None = Field(None, description="Document description")


class DocumentSetConfidentiality(BaseModel):
    """Request schema for setting document confidentiality."""

    is_confidential: bool = Field(..., description="Whether document is confidential")


class DocumentSetExpiry(BaseModel):
    """Request schema for setting document expiry."""

    expires_at: datetime | None = Field(None, description="Expiry date (None to remove expiry)")


# === Response Schemas ===

class DocumentResponse(BaseModel):
    """Response schema for document."""

    id: str = Field(..., description="Document identifier")
    tenant_id: str = Field(..., description="Tenant identifier")
    name: str = Field(..., description="Document name")
    description: str | None = Field(None, description="Document description")
    document_type: DocumentType = Field(..., description="Document type")
    status: DocumentStatus = Field(..., description="Document status")
    version: int = Field(..., description="Version number")
    is_latest: bool = Field(..., description="Whether this is the latest version")
    file_path: str | None = Field(None, description="Path to uploaded file")
    file_url: str | None = Field(None, description="External URL to document")
    file_size: int | None = Field(None, description="File size in bytes")
    mime_type: str | None = Field(None, description="MIME type")
    previous_version_id: str | None = Field(None, description="Previous version ID")
    uploaded_by: str | None = Field(None, description="User who uploaded the document")
    client_id: str | None = Field(None, description="Associated client ID")
    contract_id: str | None = Field(None, description="Associated contract ID")
    person_id: str | None = Field(None, description="Associated person ID")
    expires_at: datetime | None = Field(None, description="Expiry date")
    is_confidential: bool = Field(..., description="Whether document is confidential")
    published_at: datetime | None = Field(None, description="Publication timestamp")
    archived_at: datetime | None = Field(None, description="Archival timestamp")
    is_active: bool = Field(..., description="Whether document is active")
    created_at: datetime = Field(..., description="Creation timestamp")
    updated_at: datetime = Field(..., description="Last update timestamp")

    model_config = ConfigDict(from_attributes=True)


class DocumentListResponse(BaseModel):
    """Response schema for document list."""

    items: list[DocumentResponse] = Field(..., description="List of documents")
    total: int = Field(..., description="Total number of documents matching filters")
    page: int = Field(..., description="Current page number")
    limit: int = Field(..., description="Items per page")
    has_more: bool = Field(..., description="Whether there are more items")


class DocumentVersionResponse(BaseModel):
    """Response schema for document version history."""

    versions: list[DocumentResponse] = Field(..., description="List of document versions")
    total: int = Field(..., description="Total number of versions")
