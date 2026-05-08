"""Provider panel-management schemas (Phase 4 #D-Provider)."""

from pydantic import BaseModel, ConfigDict, Field

from app.api.schemas.base import SanitizedStr
from app.domain.enums import PanelStatus, ProviderTier


class BulkPanelStatusUpdate(BaseModel):
    provider_ids: list[str] = Field(..., min_length=1, max_length=500)
    new_status: PanelStatus
    reason: SanitizedStr = Field(..., min_length=1, max_length=500)


class BulkPanelStatusResponse(BaseModel):
    updated: list[str]
    skipped_no_change: list[str]
    not_found: list[str]
    not_provider: list[str]
    updated_count: int
    requested_count: int


class TierChangeRequest(BaseModel):
    new_tier: ProviderTier
    reason: SanitizedStr = Field(..., min_length=1, max_length=500)


class TierChangeResponse(BaseModel):
    provider_id: str
    new_tier: ProviderTier


class ProviderEligibilityResponse(BaseModel):
    provider_id: str
    client_id: str | None
    panel_eligible: bool
    binding_non_compete_count: int
    binding_non_compete_ids: list[str]
    eligible: bool
    reasons: list[str]

    model_config = ConfigDict(from_attributes=True)
