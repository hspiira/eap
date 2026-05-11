"""EAP programme + Authorization API schemas."""

from datetime import date, datetime

from pydantic import BaseModel, ConfigDict, Field

from app.api.schemas.base import OptionalSanitizedStr, SanitizedStr
from app.domain.enums import (
    AuthorizationStatus,
    RelationType,
    ServiceCategory,
)


class ProgrammeCapInput(BaseModel):
    service_category: ServiceCategory
    per_issue_per_year: int = Field(..., ge=0)
    per_year: int | None = Field(default=None, ge=0)
    per_household_per_year: int | None = Field(default=None, ge=0)


class CreateEAPProgrammeRequest(BaseModel):
    contract_id: str
    name: SanitizedStr = Field(..., min_length=1, max_length=255)
    effective_from: date
    effective_until: date | None = None
    geographic_scope: OptionalSanitizedStr = None
    description: OptionalSanitizedStr = None
    eligible_dependent_relations: list[RelationType] = []
    caps: list[ProgrammeCapInput] = Field(..., min_length=1)


class EAPProgrammeResponse(BaseModel):
    id: str
    tenant_id: str
    contract_id: str
    name: str
    effective_from: date
    effective_until: date | None
    geographic_scope: str | None
    description: str | None
    eligible_dependent_relations: list[RelationType]
    caps: list[dict]
    is_active: bool
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class AuthorizeCaseRequest(BaseModel):
    programme_id: str
    service_category: ServiceCategory
    expires_on: date | None = None


class RequestExtensionRequest(BaseModel):
    additional_sessions: int = Field(..., gt=0)


class GrantExtensionRequest(BaseModel):
    clinician_signoff_user_id: str
    admin_signoff_user_id: str


class AuthorizationResponse(BaseModel):
    id: str
    tenant_id: str
    case_id: str
    clinical_subject_id: str
    programme_id: str
    service_category: ServiceCategory
    sessions_granted: int
    sessions_used: int
    sessions_remaining: int
    status: AuthorizationStatus
    granted_at: datetime
    expires_on: date | None
    extension_requested_sessions: int | None
    extended_at: datetime | None
    closed_at: datetime | None
    created_at: datetime
    updated_at: datetime
