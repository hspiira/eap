"""
Client API Schemas (DTOs)

Pydantic models for request/response validation.
Separate from domain entities.
"""

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

from app.api.schemas.base import OptionalSanitizedStr, SanitizedStr
from app.domain.enums import BaseStatus, ClientTier, ContactMethod

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
    address: OptionalSanitizedStr = Field(None, description="Physical address")


class AddressCreate(BaseModel):
    """Address for creation."""

    street: SanitizedStr = Field(..., description="Street address")
    city: SanitizedStr = Field(..., description="City")
    country: SanitizedStr = Field(..., description="Country")
    postal_code: OptionalSanitizedStr = Field(None, description="Postal code")


class ClientCreate(BaseModel):
    """Request schema for creating a client."""

    name: SanitizedStr = Field(..., min_length=1, max_length=255, description="Client name")
    code: str = Field(
        ...,
        min_length=3,
        max_length=5,
        description="Client code (3-5 characters, unique per tenant)",
    )
    contact_info: ContactInfoCreate = Field(..., description="Contact information")
    contact_person_name: OptionalSanitizedStr = Field(
        None, description="Name of the main contact person"
    )
    billing_address: AddressCreate | None = Field(None, description="Billing address")
    industry_id: str | None = Field(None, description="Industry identifier")
    parent_client_id: str | None = Field(None, description="Parent client identifier")
    preferred_contact_method: ContactMethod | None = Field(
        None, description="Preferred contact method"
    )


class ClientSuspendRequest(BaseModel):
    """Request schema for suspending a client."""

    reason: SanitizedStr = Field(..., min_length=1, description="Suspension reason")


class ClientTerminateRequest(BaseModel):
    """Request schema for terminating a client."""

    reason: SanitizedStr = Field(..., min_length=1, description="Termination reason")


class ClientDeactivateRequest(BaseModel):
    """Request schema for deactivating a client."""

    reason: OptionalSanitizedStr = Field(None, description="Deactivation reason")


class ClientUpdate(BaseModel):
    """Request schema for an atomic client profile update."""

    name: OptionalSanitizedStr = Field(
        None, min_length=1, max_length=255, description="Client name"
    )
    preferred_contact_method: ContactMethod | None = Field(
        None, description="Preferred contact method"
    )
    tier: ClientTier | None = Field(None, description="Engagement tier (A/B/C)")
    contact_info: ContactInfoCreate | None = Field(None, description="Contact information")
    contact_person_name: OptionalSanitizedStr = Field(
        None, description="Name of the main contact person"
    )
    billing_address: AddressCreate | None = Field(None, description="Billing address")
    industry_id: str | None = Field(None, description="Industry identifier")


class ClientUpdateTier(BaseModel):
    """Request schema for updating client engagement tier."""

    tier: ClientTier | None = Field(..., description="Engagement tier; null clears it")


class ClientUpdateAliases(BaseModel):
    """Replace the human-readable aliases used to find a client."""

    aliases: list[str] = Field(default_factory=list, max_length=50)


class ClientAliasMergeRequest(BaseModel):
    """Move aliases from another client into the selected client."""

    source_client_id: str = Field(..., min_length=1, max_length=25)


class ClientTagAssignmentRequest(BaseModel):
    """Replace or extend the tags assigned to one or more clients."""

    tag_ids: list[str] = Field(default_factory=list, max_length=50)
    mode: Literal["add", "remove", "replace"] = "add"


class ClientBulkTagRequest(BaseModel):
    """Apply a tag set to selected clients."""

    client_ids: list[str] = Field(..., min_length=1, max_length=500)
    tag_ids: list[str] = Field(..., min_length=1, max_length=50)
    mode: Literal["add", "remove", "replace"] = "add"


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
    code: str = Field(..., description="Client code (3-5 characters)")
    status: BaseStatus = Field(..., description="Client status")
    is_verified: bool = Field(..., description="Whether client is verified")
    contact_info: ContactInfoSchema = Field(..., description="Contact information")
    billing_address: AddressSchema | None = Field(None, description="Billing address")
    industry_id: str | None = Field(None, description="Industry identifier")
    parent_client_id: str | None = Field(None, description="Parent client identifier")
    preferred_contact_method: ContactMethod | None = Field(
        None, description="Preferred contact method"
    )
    tier: ClientTier | None = Field(None, description="Engagement tier (A/B/C)")
    suspension_reason: str | None = Field(None, description="Reason for suspension")
    aliases: list[str] = Field(default_factory=list, description="Alternative client names")
    is_active: bool = Field(..., description="Whether client is active")
    active_contracts_count: int | None = Field(None, description="Active contracts on the client")
    staff_count: int | None = Field(None, description="Client employees on the client")
    last_activity_at: str | None = Field(None, description="Most recent client activity")
    next_renewal_date: str | None = Field(None, description="Next active contract renewal date")

    model_config = ConfigDict(from_attributes=True)


class ClientListResponse(BaseModel):
    """Response schema for client list."""

    items: list[ClientResponse] = Field(..., description="List of clients")
    total: int = Field(..., description="Total number of clients matching filters")
    page: int = Field(..., description="Current page number")
    limit: int = Field(..., description="Items per page")
    has_more: bool = Field(..., description="Whether there are more items")


class ClientSavedViewFilters(BaseModel):
    """Filters captured by a client list view."""

    search: OptionalSanitizedStr = None
    tier: ClientTier | None = None
    archived: bool = False
    parent_client_id: str | None = Field(None, max_length=25)


class ClientSavedViewCreate(BaseModel):
    """Create a named client list view."""

    name: SanitizedStr = Field(..., min_length=1, max_length=120)
    filters: ClientSavedViewFilters
    is_shared: bool = False


class ClientSavedViewResponse(BaseModel):
    """A client list view visible to its owner or tenant users when shared."""

    id: str
    tenant_id: str
    name: str
    filters: ClientSavedViewFilters
    created_by: str
    is_shared: bool
    created_at: str
    updated_at: str


class ClientSavedViewListResponse(BaseModel):
    items: list[ClientSavedViewResponse]
    total: int


class ClientDuplicateClient(BaseModel):
    id: str
    name: str
    code: str
    contact_email: str | None = None


class ClientDuplicateCandidate(BaseModel):
    first: ClientDuplicateClient
    second: ClientDuplicateClient
    reason: str
    similarity: float


class ClientDuplicateListResponse(BaseModel):
    items: list[ClientDuplicateCandidate]
    scanned: int


class ClientMergeRequest(BaseModel):
    source_client_id: str = Field(..., min_length=1, max_length=25)


class ClientMergeResponse(BaseModel):
    client: ClientResponse
    source_client_id: str
    transferred: dict[str, int]
    conflicts: list[str]


class ClientImportIssue(BaseModel):
    """A warning or validation problem found in an imported row."""

    row: int = Field(..., description="CSV row number")
    field: str | None = Field(None, description="CSV field associated with the issue")
    message: str = Field(..., description="Human-readable explanation")
    severity: str = Field("error", description="error, warning, or skipped")


class ClientImportCreated(BaseModel):
    """Identity assigned to an imported client."""

    name: str
    code: str


class ClientImportRowPreview(BaseModel):
    """Server-side classification and decision state for one imported row."""

    row: int
    name: str
    code: str | None = None
    aliases: list[str] = Field(default_factory=list)
    contact: str | None = None
    state: Literal["new", "duplicate", "similar", "invalid"]
    default_action: Literal["create", "skip"] = "create"
    matched_client_id: str | None = None
    matched_client_name: str | None = None


class ClientImportDecision(BaseModel):
    """Action selected for a row during import confirmation."""

    action: Literal["create", "skip", "merge"]
    client_id: str | None = None


class ClientImportResponse(BaseModel):
    """Result of a client CSV import."""

    imported: int
    skipped: int
    failed: int
    clients: list[ClientImportCreated]
    issues: list[ClientImportIssue]
    rows: list[ClientImportRowPreview] = Field(default_factory=list)


class ClientImportJobResponse(BaseModel):
    """Progress and result metadata for a background client import."""

    id: str
    filename: str
    status: Literal["queued", "processing", "completed", "failed"]
    file_size: int
    total_rows: int
    processed_rows: int
    imported: int
    skipped: int
    failed: int
    retry_count: int
    issues: list[ClientImportIssue] = Field(default_factory=list)
    error_message: str | None = None
    created_at: str
    started_at: str | None = None
    completed_at: str | None = None


class ClientImportJobListResponse(BaseModel):
    """Paginated import history."""

    items: list[ClientImportJobResponse]
    total: int


class ClientStatsResponse(BaseModel):
    """Response schema for client statistics."""

    client_id: str = Field(..., description="Client identifier")
    child_clients_count: int = Field(..., description="Number of child clients")
    total_contracts_count: int = Field(..., description="Total number of contracts")
    active_contracts_count: int = Field(..., description="Number of active contracts")
    employee_members_count: int = Field(..., description="Members with the Employee relation")
    spouse_members_count: int = Field(..., description="Members with the Spouse relation")
    child_members_count: int = Field(..., description="Members with the Child relation")
    other_members_count: int = Field(
        ..., description="Members with any other relation (domestic partner, other dependent)"
    )
    is_verified: bool = Field(..., description="Whether client is verified")
    status: BaseStatus = Field(..., description="Client status")
