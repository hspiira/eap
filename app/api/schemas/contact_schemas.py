"""Contact API Schemas (DTOs)."""

from pydantic import BaseModel, ConfigDict, EmailStr, Field

from app.api.schemas.base import OptionalSanitizedStr, SanitizedStr


class ContactCreate(BaseModel):
    """Request schema for creating a contact."""

    client_id: str = Field(..., description="Associated client ID")
    name: SanitizedStr = Field(..., min_length=1, max_length=255, description="Contact name")
    title: OptionalSanitizedStr = Field(None, max_length=255, description="Job title")
    email: EmailStr | None = Field(None, description="Email address")
    phone: str | None = Field(None, max_length=50, description="Phone number")
    department: OptionalSanitizedStr = Field(None, max_length=255, description="Department")
    is_primary: bool = Field(False, description="Whether this is the primary contact")
    notes: OptionalSanitizedStr = Field(None, description="Additional notes")


class ContactUpdate(BaseModel):
    """Request schema for updating a contact."""

    name: OptionalSanitizedStr = Field(None, min_length=1, max_length=255, description="Contact name")
    title: OptionalSanitizedStr = Field(None, max_length=255, description="Job title")
    email: EmailStr | None = Field(None, description="Email address")
    phone: str | None = Field(None, max_length=50, description="Phone number")
    department: OptionalSanitizedStr = Field(None, max_length=255, description="Department")
    is_primary: bool | None = Field(None, description="Whether this is the primary contact")
    notes: OptionalSanitizedStr = Field(None, description="Additional notes")


class ContactResponse(BaseModel):
    """Response schema for contact."""

    id: str = Field(..., description="Contact identifier")
    tenant_id: str = Field(..., description="Tenant identifier")
    client_id: str = Field(..., description="Associated client ID")
    name: str = Field(..., description="Contact name")
    title: str | None = Field(None, description="Job title")
    email: str | None = Field(None, description="Email address")
    phone: str | None = Field(None, description="Phone number")
    department: str | None = Field(None, description="Department")
    is_primary: bool = Field(..., description="Whether this is the primary contact")
    notes: str | None = Field(None, description="Additional notes")
    is_active: bool = Field(..., description="Whether contact is active")
    created_at: str = Field(..., description="Creation timestamp")
    updated_at: str = Field(..., description="Last update timestamp")

    model_config = ConfigDict(from_attributes=True)


class ContactListResponse(BaseModel):
    """Response schema for contact list."""

    items: list[ContactResponse] = Field(..., description="List of contacts")
    total: int = Field(..., description="Total number of contacts matching filters")
    page: int = Field(..., description="Current page number")
    limit: int = Field(..., description="Items per page")
    has_more: bool = Field(..., description="Whether there are more items")
