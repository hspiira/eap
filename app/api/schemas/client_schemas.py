"""
Client API Schemas (DTOs)

Pydantic models for request/response validation.
Separate from domain entities.
"""

from pydantic import BaseModel, ConfigDict, Field

from app.domain.enums import BaseStatus, ContactMethod


# === Value Object Schemas ===

class ContactInfoSchema(BaseModel):
    """Contact information schema."""

    phone: str | None = Field(None, description="Phone number")
    email: str | None = Field(None, description="Email address")
    address: str | None = Field(None, description="Physical address")


class AddressSchema(BaseModel):
    """Address schema."""

    street: str = Field(..., description="Street address")
    city: str = Field(..., description="City")
    country: str = Field(..., description="Country")
    postal_code: str | None = Field(None, description="Postal code")


# === Request Schemas ===

class ContactInfoCreate(BaseModel):
    """Contact information for creation."""

    phone: str | None = Field(None, description="Phone number")
    email: str | None = Field(None, description="Email address")
    address: str | None = Field(None, description="Physical address")


class AddressCreate(BaseModel):
    """Address for creation."""

    street: str = Field(..., description="Street address")
    city: str = Field(..., description="City")
    country: str = Field(..., description="Country")
    postal_code: str | None = Field(None, description="Postal code")


class ClientCreate(BaseModel):
    """Request schema for creating a client."""

    name: str = Field(..., min_length=1, max_length=255, description="Client name")
    contact_info: ContactInfoCreate = Field(..., description="Contact information")
    billing_address: AddressCreate | None = Field(None, description="Billing address")
    industry_id: str | None = Field(None, description="Industry identifier")
    parent_client_id: str | None = Field(None, description="Parent client identifier")
    preferred_contact_method: ContactMethod | None = Field(
        None, description="Preferred contact method"
    )


class ClientSuspendRequest(BaseModel):
    """Request schema for suspending a client."""

    reason: str = Field(..., min_length=1, description="Suspension reason")


class ClientTerminateRequest(BaseModel):
    """Request schema for terminating a client."""

    reason: str = Field(..., min_length=1, description="Termination reason")


class ClientDeactivateRequest(BaseModel):
    """Request schema for deactivating a client."""

    reason: str | None = Field(None, description="Deactivation reason")


class ClientUpdate(BaseModel):
    """Request schema for updating client basic information."""

    name: str | None = Field(None, min_length=1, max_length=255, description="Client name")
    preferred_contact_method: ContactMethod | None = Field(
        None, description="Preferred contact method"
    )


class ClientUpdateContactInfo(BaseModel):
    """Request schema for updating client contact information."""

    contact_info: ContactInfoCreate = Field(..., description="Contact information")


class ClientUpdateBillingAddress(BaseModel):
    """Request schema for updating client billing address."""

    billing_address: AddressCreate | None = Field(None, description="Billing address")


# === Response Schemas ===

class ClientResponse(BaseModel):
    """Response schema for client."""

    id: str = Field(..., description="Client identifier")
    tenant_id: str = Field(..., description="Tenant identifier")
    name: str = Field(..., description="Client name")
    status: BaseStatus = Field(..., description="Client status")
    is_verified: bool = Field(..., description="Whether client is verified")
    contact_info: ContactInfoSchema = Field(..., description="Contact information")
    billing_address: AddressSchema | None = Field(None, description="Billing address")
    industry_id: str | None = Field(None, description="Industry identifier")
    parent_client_id: str | None = Field(None, description="Parent client identifier")
    preferred_contact_method: ContactMethod | None = Field(
        None, description="Preferred contact method"
    )
    is_active: bool = Field(..., description="Whether client is active")

    model_config = ConfigDict(from_attributes=True)


class ClientListResponse(BaseModel):
    """Response schema for client list."""

    items: list[ClientResponse] = Field(..., description="List of clients")
    total: int = Field(..., description="Total number of clients matching filters")
    page: int = Field(..., description="Current page number")
    limit: int = Field(..., description="Items per page")
    has_more: bool = Field(..., description="Whether there are more items")


class ClientStatsResponse(BaseModel):
    """Response schema for client statistics."""

    client_id: str = Field(..., description="Client identifier")
    child_clients_count: int = Field(..., description="Number of child clients")
    total_contracts_count: int = Field(..., description="Total number of contracts")
    active_contracts_count: int = Field(..., description="Number of active contracts")
    is_verified: bool = Field(..., description="Whether client is verified")
    status: BaseStatus = Field(..., description="Client status")
