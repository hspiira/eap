"""
Person API Schemas (DTOs)

Pydantic models for request/response validation.
Separate from domain entities.
"""

from datetime import date
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

from app.domain.enums import BaseStatus, PersonType, RelationType, StaffRole, WorkStatus


# === Value Object Schemas ===

class EmploymentInfoSchema(BaseModel):
    """Employment information schema."""

    role: str = Field(..., description="Job role")
    start_date: date = Field(..., description="Employment start date")
    status: WorkStatus = Field(..., description="Work status")
    department: str | None = Field(None, description="Department")
    employee_id: str | None = Field(None, description="Employee ID")
    end_date: date | None = Field(None, description="Employment end date")


class LicenseInfoSchema(BaseModel):
    """License information schema."""

    number: str = Field(..., description="License number")
    issuing_authority: str = Field(..., description="Issuing authority")
    expiry_date: date | None = Field(None, description="License expiry date")


class StaffInfoSchema(BaseModel):
    """Staff information schema."""

    role: StaffRole = Field(..., description="Staff role")
    client_id: str = Field(..., description="Client ID")
    department: str | None = Field(None, description="Department")
    can_manage_clients: bool = Field(False, description="Can manage clients")
    can_manage_services: bool = Field(False, description="Can manage services")
    can_view_reports: bool = Field(False, description="Can view reports")


class DependentInfoSchema(BaseModel):
    """Dependent information schema."""

    primary_employee_id: str = Field(..., description="Primary employee person ID")
    relationship: RelationType = Field(..., description="Relationship type")
    guardian_id: str | None = Field(None, description="Guardian user ID")


class EmergencyContactSchema(BaseModel):
    """Emergency contact schema."""

    name: str = Field(..., description="Contact name")
    phone: str | None = Field(None, description="Phone number")
    email: str | None = Field(None, description="Email address")


# === Request Schemas ===

class PersonDeactivateRequest(BaseModel):
    """Request schema for deactivating a person."""

    reason: str | None = Field(None, description="Deactivation reason")


class PersonTerminateRequest(BaseModel):
    """Request schema for terminating a person."""

    reason: str = Field(..., min_length=1, description="Termination reason")


class AddSecondaryRoleRequest(BaseModel):
    """Request schema for adding a secondary role."""

    role: PersonType = Field(..., description="Secondary person type")
    employment_info: EmploymentInfoSchema | None = Field(
        None, description="Employment info (for CLIENT_EMPLOYEE role)"
    )
    license_info: LicenseInfoSchema | None = Field(
        None, description="License info (for SERVICE_PROVIDER role)"
    )
    staff_info: StaffInfoSchema | None = Field(
        None, description="Staff info (for PLATFORM_STAFF role)"
    )


class UpdateEmergencyContactRequest(BaseModel):
    """Request schema for updating emergency contact."""

    emergency_contact: EmergencyContactSchema = Field(
        ..., description="Emergency contact information"
    )


class UpdateEmploymentInfoRequest(BaseModel):
    """Request schema for updating employment information."""

    employment_info: EmploymentInfoSchema = Field(
        ..., description="Employment information"
    )


class UpdateLicenseInfoRequest(BaseModel):
    """Request schema for updating license information."""

    license_info: LicenseInfoSchema = Field(..., description="License information")


class UpdateStaffInfoRequest(BaseModel):
    """Request schema for updating staff information."""

    staff_info: StaffInfoSchema = Field(..., description="Staff information")


# === Response Schemas ===

class PersonResponse(BaseModel):
    """Response schema for person."""

    id: str = Field(..., description="Person identifier")
    tenant_id: str = Field(..., description="Tenant identifier")
    user_id: str = Field(..., description="User identifier")
    person_type: PersonType = Field(..., description="Primary person type")
    is_dual_role: bool = Field(..., description="Whether person has dual role")
    secondary_person_type: PersonType | None = Field(
        None, description="Secondary person type"
    )
    status: BaseStatus = Field(..., description="Person status")
    employment_info: EmploymentInfoSchema | None = Field(
        None, description="Employment information"
    )
    license_info: LicenseInfoSchema | None = Field(None, description="License information")
    staff_info: StaffInfoSchema | None = Field(None, description="Staff information")
    dependent_info: DependentInfoSchema | None = Field(
        None, description="Dependent information"
    )
    emergency_contact: EmergencyContactSchema | None = Field(
        None, description="Emergency contact"
    )
    last_service_date: date | None = Field(None, description="Last service date")
    is_eligible_for_services: bool = Field(..., description="Eligible for services")

    model_config = ConfigDict(from_attributes=True)


class PersonListResponse(BaseModel):
    """Response schema for person list."""

    items: list[PersonResponse] = Field(..., description="List of persons")
    total: int = Field(..., description="Total number of persons matching filters")
    page: int = Field(..., description="Current page number")
    limit: int = Field(..., description="Items per page")
    has_more: bool = Field(..., description="Whether there are more items")
