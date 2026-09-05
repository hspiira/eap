"""API contracts for the employer-side Members module."""

from datetime import date, datetime

from pydantic import BaseModel, ConfigDict, EmailStr, Field, model_validator

from app.api.schemas.base import OptionalSanitizedStr, SanitizedStr
from app.domain.enums import EligibilityStatus, MemberRelation


class MemberCreate(BaseModel):
    """Create a covered member; a login account is optional and separate."""

    client_id: str = Field(..., min_length=1)
    employer_member_id: SanitizedStr = Field(..., min_length=1, max_length=255)
    relation: MemberRelation
    primary_employee_member_id: str | None = None
    coverage_start: date | None = None
    coverage_end: date | None = None
    work_email: EmailStr | None = None
    personal_email: EmailStr | None = None
    display_label: SanitizedStr = Field(..., min_length=1, max_length=255)

    model_config = ConfigDict(extra="forbid")

    @model_validator(mode="after")
    def validate_relationship(self) -> "MemberCreate":
        if self.relation == MemberRelation.EMPLOYEE and self.primary_employee_member_id:
            raise ValueError("Employees cannot have a primary employee member")
        if self.relation != MemberRelation.EMPLOYEE and not self.primary_employee_member_id:
            raise ValueError("A beneficiary relation requires a primary employee member")
        if self.coverage_end and self.coverage_start and self.coverage_end < self.coverage_start:
            raise ValueError("coverage_end must be on or after coverage_start")
        return self


class MemberUpdate(BaseModel):
    """Patch current roster details. Null clears an optional field."""

    employer_member_id: SanitizedStr | None = Field(None, min_length=1, max_length=255)
    relation: MemberRelation | None = None
    primary_employee_member_id: str | None = None
    coverage_start: date | None = None
    coverage_end: date | None = None
    work_email: EmailStr | None = None
    personal_email: EmailStr | None = None
    display_label: OptionalSanitizedStr = None

    model_config = ConfigDict(extra="forbid")


class MemberResponse(BaseModel):
    id: str
    tenant_id: str
    client_id: str
    employer_member_id: str
    relation: MemberRelation
    status: EligibilityStatus
    primary_employee_member_id: str | None
    coverage_start: date | None
    coverage_end: date | None
    work_email: str | None
    personal_email: str | None
    display_label: str | None
    last_imported_at: datetime | None
    suspended_at: datetime | None
    terminated_at: datetime | None
    created_at: datetime
    updated_at: datetime
    is_currently_eligible: bool

    model_config = ConfigDict(from_attributes=True)


class MemberListResponse(BaseModel):
    items: list[MemberResponse]
    total: int
    page: int
    limit: int
    has_more: bool


class MemberDuplicateCandidate(BaseModel):
    member: MemberResponse
    matched_on: list[str]


class MemberDuplicateListResponse(BaseModel):
    candidates: list[MemberDuplicateCandidate]
