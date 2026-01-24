"""
Document API Schemas (DTOs)

Pydantic models for request/response validation.
Separate from domain entities.
"""

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from app.domain.enums import DocumentStatus, DocumentType


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

    def model_validate(cls, values):
        """Validate that either file_path or file_url is provided."""
        if not values.get("file_path") and not values.get("file_url"):
            raise ValueError("Either file_path or file_url must be provided")
        if values.get("file_path") and values.get("file_url"):
            raise ValueError("Cannot provide both file_path and file_url")
        return values


class DocumentCreateVersion(BaseModel):
    """Request schema for creating a new document version."""

    name: str | None = Field(None, min_length=1, max_length=255, description="Document name")
    description: str | None = Field(None, description="Document description")
    file_path: str | None = Field(None, max_length=500, description="Path to uploaded file")
    file_url: str | None = Field(None, max_length=500, description="External URL to document")
    file_size: int | None = Field(None, ge=0, description="File size in bytes")
    mime_type: str | None = Field(None, max_length=100, description="MIME type")

    model_config = ConfigDict(extra="forbid")

    def model_validate(cls, values):
        """Validate that either file_path or file_url is provided."""
        if not values.get("file_path") and not values.get("file_url"):
            raise ValueError("Either file_path or file_url must be provided")
        if values.get("file_path") and values.get("file_url"):
            raise ValueError("Cannot provide both file_path and file_url")
        return values


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
