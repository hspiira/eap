"""Non-compete clause API schemas (Phase 2 #D-Provider)."""

from datetime import date, datetime

from pydantic import BaseModel, ConfigDict, Field

from app.api.schemas.base import OptionalSanitizedStr, SanitizedStr
from app.domain.enums import NonCompeteStatus


class NonCompeteCreate(BaseModel):
    provider_id: str = Field(..., description="Provider person identifier")
    terms_summary: SanitizedStr = Field(..., min_length=1, description="Non-compete terms summary")
    effective_from: date = Field(..., description="Start date of the restriction")
    effective_until: date | None = Field(None, description="End date (null = indefinite)")
    document_id: OptionalSanitizedStr = Field(None, description="Linked source document id")


class NonCompeteSign(BaseModel):
    signed_by: str = Field(..., description="UserId acknowledging the signature")


class NonCompeteRevoke(BaseModel):
    reason: SanitizedStr = Field(..., min_length=1, description="Why the clause is being revoked")


class NonCompeteResponse(BaseModel):
    id: str
    tenant_id: str
    provider_id: str
    status: NonCompeteStatus
    terms_summary: str
    effective_from: date
    effective_until: date | None
    signed_at: datetime | None
    signed_by: str | None
    revoked_at: datetime | None
    revoked_reason: str | None
    document_id: str | None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
