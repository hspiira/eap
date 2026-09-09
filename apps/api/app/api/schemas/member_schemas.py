"""API contracts for the employer-side Members module."""

from datetime import date, datetime

from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator, model_validator

from app.api.schemas.base import OptionalSanitizedStr, SanitizedStr
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


class MemberCreate(BaseModel):
    """Create a covered member; a login account is optional and separate."""

    client_id: str = Field(..., min_length=1)
    employer_member_id: SanitizedStr | None = Field(
        None,
        min_length=1,
        max_length=255,
        description="Optional. Left blank, the server issues {client code}-001, -002, and so on.",
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


class MemberImportRowValues(BaseModel):
    """The raw CSV values for one roster row, as the parser read them.

    The preview echoes these back so the confirmation step can send one row at a
    time without re-uploading the file.
    """

    client_code: str | None = None
    import_source_id: str | None = None
    staff_number: str | None = None
    display_label: str | None = None
    work_email: str | None = None
    personal_email: str | None = None
    gender: str | None = None
    date_of_birth: str | None = None
    phone: str | None = None
    national_id: str | None = None
    passport_number: str | None = None
    status: str | None = None
    relation: str | None = None
    primary_import_source_id: str | None = None

    model_config = ConfigDict(extra="forbid")


class MemberImportRowPreview(BaseModel):
    row: int
    client_code: str | None
    client_name: str | None
    import_source_id: str | None
    staff_number: str | None = None
    display_label: str | None
    state: str
    message: str | None = None
    default_action: str = "import"
    values: MemberImportRowValues | None = None


class MemberImportIssue(BaseModel):
    row: int
    field: str | None = None
    message: str


class MemberImportResponse(BaseModel):
    imported: int
    skipped: int
    failed: int
    issues: list[MemberImportIssue] = Field(default_factory=list)
    rows: list[MemberImportRowPreview]


class MemberImportCommitRow(BaseModel):
    """One row the client confirmed for import, replayed from the preview."""

    row: int = Field(..., ge=1)
    values: MemberImportRowValues

    model_config = ConfigDict(extra="forbid")


class MemberImportCommitRequest(BaseModel):
    """A slice of confirmed rows. Each row is committed on its own."""

    rows: list[MemberImportCommitRow] = Field(..., min_length=1, max_length=100)

    model_config = ConfigDict(extra="forbid")


class MemberImportRowResult(BaseModel):
    """What happened to a single row once it was written."""

    row: int
    state: str
    member_id: str | None = None
    message: str | None = None


class MemberImportCommitResponse(BaseModel):
    results: list[MemberImportRowResult]
