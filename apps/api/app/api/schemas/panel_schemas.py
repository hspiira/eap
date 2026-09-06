"""Provider panel-management schemas (Phase 4 #D-Provider)."""

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from app.api.schemas.base import NonBlankReason
from app.domain.enums import PanelStatus, ProviderTier


class BulkPanelStatusUpdate(BaseModel):
    provider_ids: list[str] = Field(..., min_length=1, max_length=500)
    new_status: PanelStatus
    reason: NonBlankReason


class BulkPanelStatusResponse(BaseModel):
    updated: list[str]
    skipped_no_change: list[str]
    not_found: list[str]
    not_provider: list[str]
    updated_count: int
    requested_count: int


class TierChangeRequest(BaseModel):
    new_tier: ProviderTier
    reason: NonBlankReason


class TierChangeResponse(BaseModel):
    provider_id: str
    new_tier: ProviderTier


class EligibilityFailure(BaseModel):
    code: str
    message: str


class ProviderEligibilityResponse(BaseModel):
    """Preview of the booking gate.

    ``eligible`` is the same rule the write paths apply, so a preview cannot
    disagree with the booking it precedes. The non-compete counts are retained
    for compatibility and are informational: non-compete is not live and does
    not restrict booking.
    """

    provider_id: str
    client_id: str | None
    scheduled_at: datetime
    panel_eligible: bool
    binding_non_compete_count: int
    binding_non_compete_ids: list[str]
    eligible: bool
    reasons: list[str]
    failures: list[EligibilityFailure]

    model_config = ConfigDict(from_attributes=True)
