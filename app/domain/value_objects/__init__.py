"""
Value Objects

Immutable domain concepts identified by their value, not identity.
Self-validating and encapsulating domain rules.
"""

from app.domain.value_objects.audit import FieldChange
from app.domain.value_objects.core import (
    Address,
    AuditLogId,
    ClientId,
    ContactInfo,
    ContractId,
    DateRange,
    DependentInfo,
    Email,
    EmploymentInfo,
    EmergencyContact,
    EntityChangeId,
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
    "AuditLogId",
    "ClientId",
    "ContactInfo",
    "ContractId",
    "DateRange",
    "DependentInfo",
    "Email",
    "EmploymentInfo",
    "EmergencyContact",
    "EntityChangeId",
    "FieldChange",
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
