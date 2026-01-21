"""
Value Objects

Immutable domain concepts identified by their value, not identity.
Self-validating and encapsulating domain rules.
"""

from app.domain.value_objects.core import (
    Address,
    ClientId,
    ContactInfo,
    ContractId,
    DateRange,
    DependentInfo,
    Email,
    EmploymentInfo,
    EmergencyContact,
    Id,
    IndustryId,
    LicenseInfo,
    Money,
    PersonId,
    ServiceId,
    SessionId,
    StaffInfo,
    TenantCode,
    TenantId,
    TenantSettings,
    UserId,
)

__all__ = [
    "Address",
    "ClientId",
    "ContactInfo",
    "ContractId",
    "DateRange",
    "DependentInfo",
    "Email",
    "EmploymentInfo",
    "EmergencyContact",
    "Id",
    "IndustryId",
    "LicenseInfo",
    "Money",
    "PersonId",
    "ServiceId",
    "SessionId",
    "StaffInfo",
    "TenantCode",
    "TenantId",
    "TenantSettings",
    "UserId",
]
