"""Provider profile API schemas (Phase 2 #D-Provider)."""

from datetime import date

from pydantic import BaseModel, ConfigDict, Field

from app.api.schemas.base import OptionalSanitizedStr
from app.domain.enums import (
    AccreditationStatus,
    PanelStatus,
    ProviderGender,
    ProviderTier,
    ProviderTitle,
    UgandaRegion,
)


class ProviderProfileSchema(BaseModel):
    tier: ProviderTier | None = None
    region: UgandaRegion | None = None
    accreditation_status: AccreditationStatus
    panel_status: PanelStatus = PanelStatus.ACTIVE
    accreditation_authority: OptionalSanitizedStr = None
    accreditation_expiry: date | None = None
    specialties: list[str] = Field(default_factory=list)
    bio: OptionalSanitizedStr = None
    gender: ProviderGender | None = None
    title: ProviderTitle | None = None

    model_config = ConfigDict(from_attributes=True)


class ProviderProfileUpdate(BaseModel):
    profile: ProviderProfileSchema = Field(..., description="Replacement provider profile")
