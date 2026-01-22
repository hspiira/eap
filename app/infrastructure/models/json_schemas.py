"""
JSON Schema Definitions for Database Models

TypedDict structures for JSON columns to provide type safety and validation.
These match the serialized format of domain value objects.
"""

from typing import TypedDict, NotRequired


class EmploymentInfoDict(TypedDict):
    """
    JSON schema for employment_info column.
    
    Represents employment information for CLIENT_EMPLOYEE person types.
    
    Fields:
        role: Job title or role name (required)
        start_date: Employment start date in ISO format (YYYY-MM-DD) (required)
        status: Work status enum value (e.g., "Active", "Inactive") (required)
        department: Department name (optional)
        employee_id: Employee identifier (optional)
        end_date: Employment end date in ISO format (YYYY-MM-DD) (optional)
    """
    role: str
    start_date: str  # ISO date format: YYYY-MM-DD
    status: str  # WorkStatus enum value
    department: NotRequired[str | None]
    employee_id: NotRequired[str | None]
    end_date: NotRequired[str | None]  # ISO date format: YYYY-MM-DD


class LicenseInfoDict(TypedDict):
    """
    JSON schema for license_info column.
    
    Represents professional license information for SERVICE_PROVIDER person types.
    
    Fields:
        number: License number (required)
        issuing_authority: Authority that issued the license (required)
        expiry_date: License expiration date in ISO format (YYYY-MM-DD) (optional)
    """
    number: str
    issuing_authority: str
    expiry_date: NotRequired[str | None]  # ISO date format: YYYY-MM-DD


class StaffInfoDict(TypedDict):
    """
    JSON schema for staff_info column.
    
    Represents staff information for PLATFORM_STAFF person types.
    
    Fields:
        role: Staff role enum value (e.g., "Admin", "Manager") (required)
        client_id: Associated client identifier (required)
        department: Department name (optional)
        can_manage_clients: Permission to manage clients (default: false)
        can_manage_services: Permission to manage services (default: false)
        can_view_reports: Permission to view reports (default: false)
    """
    role: str  # StaffRole enum value
    client_id: str
    department: NotRequired[str | None]
    can_manage_clients: NotRequired[bool]
    can_manage_services: NotRequired[bool]
    can_view_reports: NotRequired[bool]


class DependentInfoDict(TypedDict):
    """
    JSON schema for dependent_info column.
    
    Represents dependent information for DEPENDENT person types.
    
    Fields:
        primary_employee_id: ID of the primary employee (required)
        relationship: Relationship type enum value (e.g., "Child", "Spouse") (required)
        guardian_id: Guardian user ID (optional)
    """
    primary_employee_id: str
    relationship: str  # RelationType enum value
    guardian_id: NotRequired[str | None]


class EmergencyContactDict(TypedDict):
    """
    JSON schema for emergency_contact column.
    
    Represents emergency contact information (shared across person types).
    
    Fields:
        name: Contact name (required)
        phone: Phone number (optional, but phone or email required)
        email: Email address (optional, but phone or email required)
    """
    name: str
    phone: NotRequired[str | None]
    email: NotRequired[str | None]
