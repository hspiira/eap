"""API contracts for the employer-side Members module."""

from datetime import date, datetime

from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator, model_validator

from app.api.schemas.base import OptionalSanitizedStr, SanitizedStr
from app.domain.enums import (
    EligibilityStatus,
    MemberGender,
    MemberRelation,
    NextOfKinRelationship,
)


class MemberNextOfKinCreate(BaseModel):
    name: SanitizedStr = Field(..., min_length=1, max_length=255)
    relationship: NextOfKinRelationship
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
    relationship: NextOfKinRelationship
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
    work_email: str | None
    personal_email: str | None
    display_label: str | None
    date_of_birth: date | None
    gender: MemberGender | None
    phone: str | None
    staff_number: str | None = None
    national_id: str | None = None
    passport_number: str | None = None
    last_imported_at: datetime | None
    suspended_at: datetime | None
    terminated_at: datetime | None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class MemberListResponse(BaseModel):
    items: list[MemberResponse]
    total: int
    page: int
    limit: int
    has_more: bool
