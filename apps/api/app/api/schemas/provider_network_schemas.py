"""API contracts for organisations, affiliations, vocabulary and staged imports."""

from datetime import date, datetime
from typing import Annotated

from pydantic import AfterValidator, BaseModel, ConfigDict, EmailStr, Field

from app.api.schemas.base import OptionalSanitizedStr, SanitizedStr
from app.domain.enums.provider_network import (
    AliasResolutionState,
    DeliveryContext,
    ImportBatchStatus,
    ImportRowOutcome,
    OrganisationApprovalStatus,
)


def _require_non_blank(value: str) -> str:
    """Reject a value that is only whitespace.

    `min_length` alone is checked before stripping, so "   " passed the length
    constraint and then became an empty reason.
    """
    stripped = value.strip()
    if not stripped:
        raise ValueError("must not be blank")
    return stripped


def _non_blank(max_length: int):
    """A required text field that rejects whitespace-only input as a 422."""
    return Annotated[SanitizedStr, Field(max_length=max_length), AfterValidator(_require_non_blank)]


NonBlankStr = _non_blank(500)
NonBlankName = _non_blank(255)
NonBlankCode = _non_blank(100)


class ReasonRequest(BaseModel):
    """Every lifecycle command records why, per decision 8.

    Whitespace is stripped before the length check, so a reason of spaces is a
    422 from the schema rather than a 400 from the domain.
    """

    reason: NonBlankStr


class ProviderOrganisationCreate(BaseModel):
    name: NonBlankName
    registration_number: OptionalSanitizedStr = Field(None, max_length=100)
    contact_email: EmailStr | None = None
    contact_phone: OptionalSanitizedStr = Field(None, max_length=50)


class ProviderOrganisationUpdate(BaseModel):
    """Partial update. An explicit null clears an optional field.

    `is_active` and `approval_status` are deliberately absent: they move only
    through the audited lifecycle commands.
    """

    name: OptionalSanitizedStr = Field(None, min_length=1, max_length=255)
    registration_number: OptionalSanitizedStr = Field(None, max_length=100)
    contact_email: EmailStr | None = None
    contact_phone: OptionalSanitizedStr = Field(None, max_length=50)


class ProviderOrganisationResponse(BaseModel):
    id: str
    tenant_id: str
    name: str
    registration_number: str | None
    contact_email: str | None
    contact_phone: str | None
    is_active: bool
    approval_status: OrganisationApprovalStatus
    created_at: datetime
    updated_at: datetime
    model_config = ConfigDict(from_attributes=True)


class ProviderOrganisationListResponse(BaseModel):
    items: list[ProviderOrganisationResponse]
    total: int
    page: int
    limit: int
    has_more: bool


class ProviderAffiliationCreate(BaseModel):
    """`valid_until` is exclusive: the last covered day is the day before."""

    provider_id: str = Field(..., min_length=1, max_length=25)
    valid_from: date
    valid_until: date | None = None


class ProviderAffiliationEndUpdate(ReasonRequest):
    """Only the end date moves. The practitioner and organisation are immutable."""

    valid_until: date | None = None


class ProviderAffiliationResponse(BaseModel):
    id: str
    tenant_id: str
    provider_id: str
    organisation_id: str
    valid_from: date
    valid_until: date | None
    organisation_name: str
    organisation_is_active: bool
    organisation_approval_status: OrganisationApprovalStatus
    created_at: datetime
    updated_at: datetime


class ProviderAffiliationListResponse(BaseModel):
    items: list[ProviderAffiliationResponse]
    total: int
    page: int
    limit: int
    has_more: bool


class ProviderSpecialtyResponse(BaseModel):
    id: str
    code: str
    label: str
    is_active: bool
    model_config = ConfigDict(from_attributes=True)


class ProviderSpecialtyCreate(BaseModel):
    code: NonBlankCode
    label: NonBlankName


class ProviderSpecialtyLinkCreate(BaseModel):
    provider_id: str = Field(..., min_length=1, max_length=25)
    specialty_id: str = Field(..., min_length=1, max_length=25)


class ProviderSpecialtyLinkResponse(BaseModel):
    id: str
    tenant_id: str
    provider_id: str
    specialty_id: str
    specialty_code: str
    specialty_label: str
    specialty_is_active: bool


class ProviderAliasResponse(BaseModel):
    id: str
    tenant_id: str
    source_system: str
    source_value: str
    normalized_value: str
    state: AliasResolutionState
    provider_id: str | None
    candidate_provider_ids: list[str]
    review_note: str | None
    created_at: datetime
    updated_at: datetime


class ProviderAliasListResponse(BaseModel):
    items: list[ProviderAliasResponse]
    total: int
    page: int
    limit: int
    has_more: bool


class ProviderAliasResolveRequest(BaseModel):
    """Explicit reconciliation. There is no automatic resolution endpoint."""

    provider_id: str = Field(..., min_length=1, max_length=25)


class ProviderAliasRejectRequest(BaseModel):
    note: NonBlankStr


class SessionImportRowPreview(BaseModel):
    row_number: int
    outcome: ImportRowOutcome
    delivery_context: DeliveryContext
    provider_id: str | None
    provider_affiliation_id: str | None
    raw_practitioner_name: str | None
    session_date: date | None
    reasons: list[str]


class SessionImportBatchResponse(BaseModel):
    id: str
    tenant_id: str
    source_system: str
    file_name: str
    file_hash: str
    row_count: int
    source_record_key_field: str | None
    status: ImportBatchStatus
    outcome_counts: dict[str, int]
    created_at: datetime
    applied_at: datetime | None


class SessionImportRowListResponse(BaseModel):
    items: list[SessionImportRowPreview]
    total: int
    page: int
    limit: int
    has_more: bool
