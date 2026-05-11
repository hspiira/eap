"""Eligible-member API schemas (Phase 5A #5A.1)."""

from datetime import date, datetime

from pydantic import BaseModel, ConfigDict, EmailStr, Field

from app.api.schemas.base import OptionalSanitizedStr, SanitizedStr
from app.domain.enums import EligibilityStatus, MemberRelation


class EligibleMemberEnrol(BaseModel):
    client_id: str
    employer_member_id: SanitizedStr = Field(..., min_length=1, max_length=255)
    relation: MemberRelation
    primary_employee_member_id: str | None = None
    coverage_start: date | None = None
    coverage_end: date | None = None
    work_email: EmailStr | None = None
    personal_email: EmailStr | None = None
    display_label: OptionalSanitizedStr = None


class EligibleMemberResponse(BaseModel):
    id: str
    tenant_id: str
    client_id: str
    employer_member_id: str
    relation: MemberRelation
    status: EligibilityStatus
    primary_employee_member_id: str | None
    coverage_start: date | None
    coverage_end: date | None
    display_label: str | None
    last_imported_at: datetime | None
    suspended_at: datetime | None
    terminated_at: datetime | None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class ClinicalSubjectResponse(BaseModel):
    """Returned only via clinical-scope routes; carries no PII by construction."""

    id: str
    tenant_id: str
    pseudonym: str
    preferred_language: str | None
    preferred_pronouns: str | None
    preferred_contact_method: str | None
    is_active: bool
    deactivated_at: datetime | None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
