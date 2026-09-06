"""Practitioner API contracts.

A practitioner owns their display name and optional contact details. ``email``
is the practitioner's contact address, not a login: an account link is optional
and is managed only through the account-link commands.

Panel, tier, accreditation and activation are not writable here. They change
only through the lifecycle commands, each of which requires a reason.

Specialties are not writable here either. Decision 5 makes a tenant's link to
the global catalogue the only way to record one, so that selecting a retired
entry can be refused and an id rather than a name establishes identity. The
response still carries the stored list until phase 4 projects it from those
links; treat it as read-only.
"""

from datetime import date, datetime

from pydantic import BaseModel, ConfigDict, EmailStr, Field, model_validator

from app.api.schemas.base import NonBlankReason, OptionalSanitizedStr, SanitizedStr
from app.api.schemas.provider_profile_schemas import ProviderProfileSchema
from app.domain.enums import (
    AccreditationStatus,
    BaseStatus,
    PanelStatus,
    ProviderIdentityProvenance,
    ProviderTier,
    UgandaRegion,
)

PROTECTED_FIELDS = {
    "provider_profile": "PATCH /providers/{id} cannot replace the whole profile",
    "specialties": "use the provider-specialty link endpoints",
    "tier": "use PATCH /providers/{id}/tier",
    "panel_status": "use PATCH /providers/{id}/panel-status",
    "accreditation_status": "use PATCH /providers/{id}/accreditation",
    "accreditation_authority": "use PATCH /providers/{id}/accreditation",
    "accreditation_expiry": "use PATCH /providers/{id}/accreditation",
    "status": "use PATCH /providers/{id}/status",
    "user_id": "use POST or DELETE /providers/{id}/account-link",
}


class ProviderResponse(BaseModel):
    id: str
    tenant_id: str
    display_name: str
    email: str | None = Field(None, description="Practitioner contact email, not a login")
    phone: str | None = None
    user_id: str | None = Field(None, description="Linked account, if any")
    identity_provenance: ProviderIdentityProvenance
    status: BaseStatus
    license_info: dict | None = None
    provider_profile: ProviderProfileSchema
    created_at: datetime
    updated_at: datetime
    model_config = ConfigDict(from_attributes=True)


class ProviderCreate(BaseModel):
    """Create a practitioner. No account is linked and no lifecycle field is set."""

    display_name: SanitizedStr = Field(..., min_length=1, max_length=200)
    email: EmailStr | None = None
    phone: OptionalSanitizedStr = Field(None, max_length=50)
    tier: ProviderTier
    region: UgandaRegion
    bio: OptionalSanitizedStr = None
    license_info: dict | None = None

    model_config = ConfigDict(extra="forbid")


class ProviderUpdate(BaseModel):
    """Partial update of ordinary contact and profile fields.

    An omitted field stays unchanged; an explicit null clears a nullable field.
    A protected field present in the body is rejected rather than ignored.
    """

    display_name: SanitizedStr | None = Field(None, min_length=1, max_length=200)
    email: EmailStr | None = None
    phone: OptionalSanitizedStr = Field(None, max_length=50)
    region: UgandaRegion | None = None
    bio: OptionalSanitizedStr = None
    license_info: dict | None = None

    model_config = ConfigDict(extra="forbid")

    @model_validator(mode="before")
    @classmethod
    def _reject_protected_fields(cls, data: object) -> object:
        if not isinstance(data, dict):
            return data
        offending = [name for name in PROTECTED_FIELDS if name in data]
        if offending:
            raise ValueError(
                "These fields cannot be changed through a general update: "
                + "; ".join(f"{name} ({PROTECTED_FIELDS[name]})" for name in offending)
            )
        if "display_name" in data and data["display_name"] is None:
            raise ValueError("display_name is required and cannot be cleared")
        return data

    @model_validator(mode="after")
    def _require_one_field(self) -> "ProviderUpdate":
        if not self.model_fields_set:
            raise ValueError("At least one field must be provided for update")
        return self


class TierCommand(BaseModel):
    tier: ProviderTier
    reason: NonBlankReason


class PanelStatusCommand(BaseModel):
    panel_status: PanelStatus
    reason: NonBlankReason


class AccreditationCommand(BaseModel):
    accreditation_status: AccreditationStatus
    accreditation_authority: OptionalSanitizedStr = Field(None, max_length=200)
    accreditation_expiry: date | None = None
    reason: NonBlankReason


class StatusCommand(BaseModel):
    status: BaseStatus
    reason: NonBlankReason


class AccountLinkCommand(BaseModel):
    user_id: str
    reason: NonBlankReason


class AccountUnlinkCommand(BaseModel):
    reason: NonBlankReason


class ProviderListResponse(BaseModel):
    items: list[ProviderResponse]
    total: int = Field(..., description="Count over the whole filtered dataset")
    page: int
    limit: int
    has_more: bool
