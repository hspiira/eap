"""API contracts for the employer-side Members module."""

from datetime import date, datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator, model_validator

from app.api.schemas.base import NonBlankReason, OptionalSanitizedStr, SanitizedStr
from app.domain.enums import (
    EligibilityStatus,
    MemberGender,
    MemberRelation,
)


class MemberNextOfKinCreate(BaseModel):
    name: SanitizedStr = Field(..., min_length=1, max_length=255)
    relationship: str
    phone: SanitizedStr | None = Field(None, max_length=50)
    email: EmailStr | None = None
    is_primary: bool = False

    model_config = ConfigDict(extra="forbid")

    @field_validator("name", mode="before")
    @classmethod
    def validate_name(cls, value: str) -> str:
        if not isinstance(value, str) or not value.strip():
            raise ValueError("Next-of-kin name is required")
        return value

    @model_validator(mode="after")
    def validate_contact_method(self) -> "MemberNextOfKinCreate":
        if not self.phone and not self.email:
            raise ValueError("Next-of-kin needs phone or email")
        return self


class MemberNextOfKinUpdate(MemberNextOfKinCreate):
    pass


class MemberNextOfKinResponse(BaseModel):
    id: str
    tenant_id: str
    member_id: str
    name: str
    relationship: str
    phone: str | None
    email: str | None
    is_primary: bool
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class MemberEmployment(BaseModel):
    """Optional workforce attributes from the employer's roster.

    Free text: the vocabularies are the employer's own. Held for record and
    segmentation only, and read by no eligibility rule.
    """

    job_title: OptionalSanitizedStr = Field(None, max_length=255)
    job_classification: OptionalSanitizedStr = Field(None, max_length=255)
    skill: OptionalSanitizedStr = Field(None, max_length=255)
    department: OptionalSanitizedStr = Field(None, max_length=255)
    unit: OptionalSanitizedStr = Field(None, max_length=255)
    employment_type: OptionalSanitizedStr = Field(
        None,
        max_length=255,
        description=(
            "The employee's contract of employment (e.g. Permanent, FTC). "
            "Unrelated to the client's commercial contract."
        ),
    )

    model_config = ConfigDict(extra="forbid")


class MemberCreate(BaseModel):
    """Create a covered member; a login account is optional and separate."""

    client_id: str = Field(..., min_length=1)
    employer_member_id: SanitizedStr | None = Field(
        None,
        min_length=1,
        max_length=255,
        description=(
            "Do not set on create; the server always issues {client code}-001, -002, "
            "and so on. Reused internally to revalidate a PATCH that changes it."
        ),
    )
    relation: MemberRelation
    primary_employee_member_id: str | None = None
    import_source_id: SanitizedStr | None = Field(
        None,
        max_length=255,
        description=(
            "Optional. The employer's own reference for this row (e.g. a roster "
            "Staff_ID), used to match rows on re-import. Never the member code."
        ),
    )
    work_email: EmailStr | None = None
    personal_email: EmailStr | None = None
    display_label: SanitizedStr = Field(..., min_length=1, max_length=255)
    date_of_birth: date | None = None
    gender: MemberGender | None = None
    phone: SanitizedStr | None = Field(None, max_length=50)
    staff_number: SanitizedStr | None = Field(None, max_length=100)
    national_id: SanitizedStr | None = Field(None, max_length=100)
    passport_number: SanitizedStr | None = Field(None, max_length=100)
    employment: MemberEmployment | None = None

    model_config = ConfigDict(extra="forbid")

    @field_validator("display_label", mode="before")
    @classmethod
    def validate_name(cls, value: str) -> str:
        if not isinstance(value, str) or not value.strip():
            raise ValueError("Member name is required")
        return value

    @field_validator("date_of_birth")
    @classmethod
    def validate_date_of_birth(cls, value: date | None) -> date | None:
        if value and value > date.today():
            raise ValueError("Date of birth cannot be in the future")
        return value

    @model_validator(mode="after")
    def validate_relationship(self) -> "MemberCreate":
        if self.relation == MemberRelation.EMPLOYEE and self.primary_employee_member_id:
            raise ValueError("Employees cannot have a primary employee member")
        if self.relation != MemberRelation.EMPLOYEE and not self.primary_employee_member_id:
            raise ValueError("A beneficiary relation requires a primary employee member")
        return self


class MemberUpdate(BaseModel):
    """Patch current roster details. Null clears an optional field."""

    employer_member_id: SanitizedStr | None = Field(None, min_length=1, max_length=255)
    relation: MemberRelation | None = None
    primary_employee_member_id: str | None = None
    work_email: EmailStr | None = None
    personal_email: EmailStr | None = None
    display_label: OptionalSanitizedStr = None
    date_of_birth: date | None = None
    gender: MemberGender | None = None
    phone: SanitizedStr | None = Field(None, max_length=50)
    staff_number: SanitizedStr | None = Field(None, max_length=100)
    national_id: SanitizedStr | None = Field(None, max_length=100)
    passport_number: SanitizedStr | None = Field(None, max_length=100)
    employment: MemberEmployment | None = None

    model_config = ConfigDict(extra="forbid")

    @field_validator("display_label", mode="before")
    @classmethod
    def validate_name(cls, value: str | None) -> str | None:
        if not isinstance(value, str) or not value.strip():
            raise ValueError("Member name cannot be blank")
        return value

    @field_validator("date_of_birth")
    @classmethod
    def validate_date_of_birth(cls, value: date | None) -> date | None:
        if value and value > date.today():
            raise ValueError("Date of birth cannot be in the future")
        return value


class MemberResponse(BaseModel):
    id: str
    tenant_id: str
    client_id: str
    client_name: str | None = None
    employer_member_id: str
    relation: MemberRelation
    status: EligibilityStatus
    primary_employee_member_id: str | None
    coverage_start: date | None = None
    coverage_end: date | None = None
    is_currently_eligible: bool
    work_email: str | None
    personal_email: str | None
    display_label: str | None
    date_of_birth: date | None
    gender: MemberGender | None
    phone: str | None
    staff_number: str | None = None
    import_source_id: str | None = None
    national_id: str | None = None
    passport_number: str | None = None
    employment: MemberEmployment | None = None
    last_imported_at: datetime | None
    suspended_at: datetime | None
    terminated_at: datetime | None
    created_at: datetime
    updated_at: datetime
    user_id: str | None = None

    model_config = ConfigDict(from_attributes=True)


class MemberStatsResponse(BaseModel):
    total: int
    active: int
    suspended: int
    pending: int
    terminated: int
    with_account: int


class MemberListResponse(BaseModel):
    items: list[MemberResponse]
    total: int
    page: int
    limit: int
    has_more: bool


class MemberAccountLinkRequest(BaseModel):
    user_id: str = Field(..., min_length=1)


class MemberMergeRequest(BaseModel):
    source_member_id: str = Field(..., min_length=1)


class MemberMergeResponse(BaseModel):
    member: MemberResponse
    source_member_id: str
    transferred: dict[str, int]


class MemberDuplicateMember(BaseModel):
    id: str
    client_id: str
    client_name: str | None = None
    employer_member_id: str
    display_label: str
    relation: MemberRelation


class MemberDuplicateCandidate(BaseModel):
    first: MemberDuplicateMember
    second: MemberDuplicateMember
    reason: str


class MemberDuplicateListResponse(BaseModel):
    items: list[MemberDuplicateCandidate]
    scanned: int


class MemberImportBatchResponse(BaseModel):
    """One staged roster upload and its outcome counts."""

    id: str
    tenant_id: str
    file_name: str
    file_hash: str
    row_count: int
    status: str
    outcome_counts: dict[str, int]
    staged_by: str
    applied_by: str | None = None
    applied_at: datetime | None = None
    created_at: datetime


class MemberImportRowResponse(BaseModel):
    """One staged row: what it resolved to, and what a person decided about it."""

    id: str
    row_number: int
    client_code: str | None
    client_name: str | None = None
    import_source_id: str | None
    staff_number: str | None = None
    display_label: str | None
    outcome: str
    decision: str
    message: str | None = None
    imported_member_id: str | None = None


class MemberImportRowListResponse(BaseModel):
    items: list[MemberImportRowResponse]
    total: int
    page: int
    limit: int
    has_more: bool


class MemberImportRowDecisionRequest(BaseModel):
    """Override one still-new row's Import/Skip decision before applying."""

    decision: Literal["import", "skip"]

    model_config = ConfigDict(extra="forbid")


class MemberImportAbandonRequest(BaseModel):
    """Why nobody will apply this batch. It goes on the record, so it is required."""

    reason: NonBlankReason

    model_config = ConfigDict(extra="forbid")


class MemberImportApplyResponse(BaseModel):
    """What happened when a staged batch's importable rows were written."""

    batch_id: str
    imported: int
    failed: int
    skipped_already_imported: int
    not_importable: int
