"""
Domain value objects for the Evexía core domain.

Value objects are immutable types that represent domain concepts with self-validation.
They have no identity, only value.
"""

from dataclasses import dataclass
from datetime import date, datetime
import decimal
import re
from app.domain.enums import WorkStatus, StaffRole, RelationType
from app.domain.enums import WorkStatus, StaffRole, RelationType
from app.shared.utils.datetime import utc_now


@dataclass(frozen=True)
class TenantCode:
    """
    Represents a unique code for a tenant.

    Attributes:
    - 3-15 characters
    - lowercase
    - alphanumeric with optional hyphen
    - abbreviation-based (not full legal names)
    - immutable once activated
    """
    value: str

    def __post_init__(self):
        if not self.value:
            raise ValueError("Tenant code must be a non-empty string")

        # Length validation
        if len(self.value) < 3 or len(self.value) > 15:
            raise ValueError("Tenant code must be 3-15 characters")

        # Format validation: lowercase alphanumeric with optional hyphens
        if not re.match(r"^[a-z0-9]+(-[a-z0-9]+)*$", self.value):
            raise ValueError(
                "Tenant code must be lowercase alphanumeric with optional hyphens "
                "(e.g., 'acme', 'acme-corp', 'abc123')"
            )

# === Identity Value Objects ===

@dataclass(frozen=True)
class Id:
    """
    Represents a unique identifier for an entity.

    Attributes:
    - <25 characters
    - immutable once activated
    """
    value: str
    def __post_init__(self):
        if not self.value or len(self.value) > 25:
            raise ValueError("ID must be less than 25 characters")

TenantId = Id
PersonId = Id
ContractId = Id
ServiceId = Id
SessionId = Id
UserId = Id
ClientId = Id
IndustryId = Id
AuditLogId = Id
EntityChangeId = Id
DocumentId = Id
KPIId = Id
KPIAssignmentId = Id
ClientTagId = Id
ContactId = Id
ActivityId = Id
ServiceAssignmentId = Id

# === Domain Value Objects ===
@dataclass(frozen=True)
class Email:
    """
    Represents an email address.

    Attributes:
    - <255 characters
    - email address format
    - immutable once activated
    """
    value: str
    def __post_init__(self):
        if not self.value or len(self.value) > 255:
            raise ValueError("Email must be less than 255 characters")
        if not re.match(r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$", self.value):
            raise ValueError("Invalid email address format")

@dataclass(frozen=True)
class Money:
    amount: decimal.Decimal
    currency: str
    def __post_init__(self):
        if self.amount < 0:
            raise ValueError("Amount must be a positive number")
        if not self.currency or len(self.currency) != 3:
            raise ValueError("Currency must be a 3-letter ISO code")
    def add(self, other: 'Money') -> 'Money':
        if self.currency != other.currency:
            raise ValueError("Currencies must be the same")
        return Money(self.amount + other.amount, self.currency)
    def subtract(self, other: 'Money') -> 'Money':
        if self.currency != other.currency:
            raise ValueError("Currencies must be the same")
        return Money(self.amount - other.amount, self.currency)
    def multiply(self, factor: decimal.Decimal) -> 'Money':
        return Money(self.amount * factor, self.currency)
    def divide(self, divisor: decimal.Decimal) -> 'Money':
        if divisor == 0:
            raise ValueError("Division by zero")
        return Money(self.amount / divisor, self.currency)

@dataclass(frozen=True)
class DateRange:
    start_date: datetime
    end_date: datetime
    def __post_init__(self):
        if self.start_date > self.end_date:
            raise ValueError("Start date must be before end date")
    @property
    def days(self) -> int:
        return (self.end_date - self.start_date).days
    @property
    def months(self) -> int:
        return (self.end_date.year - self.start_date.year) * 12 + (self.end_date.month - self.start_date.month)
    @property
    def years(self) -> int:
        return self.end_date.year - self.start_date.year
    def contains(self, date: datetime) -> bool:
        return self.start_date <= date <= self.end_date
    def extend_to(self, new_end: datetime) -> 'DateRange':
        return DateRange(self.start_date, new_end)

@dataclass(frozen=True)
class TenantSettings:
    """
    Represents tenant settings.

    Attributes:
    - max_users: Maximum number of users
    - max_clients: Maximum number of clients
    - features_enabled: Enabled features
    - custom_branding: Whether custom branding is enabled
    """
    max_users: int
    max_clients: int
    features_enabled: tuple[str, ...]
    custom_branding: bool=False
    def __post_init__(self) -> None:
        if self.max_users < 0:
            raise ValueError("Max users must be greater than zero")
        if self.max_clients < 0:
            raise ValueError("Max clients must be greater than zero")
    def allows_more_users(self, current_count: int) -> bool:
        return current_count < self.max_users

    def allows_more_clients(self, current_count: int) -> bool:
        return current_count < self.max_clients

@dataclass(frozen=True)
class ContactInfo:
    phone: str | None = None
    email: Email | None = None
    address: str | None = None
    def has_any_contact(self) -> bool:
        return bool(self.phone or self.email or self.address)

@dataclass(frozen=True)
class Address:
    street: str
    city: str
    country: str
    postal_code: str | None = None
    def __post_init__(self):
        if not self.street or not self.city or not self.country:
            raise ValueError("Address requires street, city, country")

@dataclass(frozen=True)
class EmergencyContact:
    name: str
    phone: str | None = None
    email: Email | None = None
    def __post_init__(self):
        if not self.name:
            raise ValueError("Emergency contact name required")
        # Validate that at least one of phone or email is non-empty
        # (not None and not empty string)
        phone_provided = bool(self.phone and self.phone.strip())
        email_provided = self.email is not None
        if not phone_provided and not email_provided:
            raise ValueError("Emergency contact needs phone or email")

@dataclass(frozen=True)
class LicenseInfo:
    number: str
    issuing_authority: str
    expiry_date: date | None = None
    def __post_init__(self):
        if not self.number or not self.issuing_authority:
            raise ValueError("License number and authority required")
    def is_valid(self) -> bool:
        if not self.expiry_date:
            return True
        return self.expiry_date >= utc_now().date()

@dataclass(frozen=True)
class ClientEmployeeCode:
    client_code: str
    family_code: str
    member_code: str
    
    def __post_init__(self):
        if not self.client_code or len(self.client_code) < 3 or len(self.client_code) > 5:
            raise ValueError("Client code must be 3-5 characters")
        if not self.family_code or len(self.family_code) != 2:
            raise ValueError("Family code must be 2 digits")
        if not self.member_code or len(self.member_code) != 2:
            raise ValueError("Member code must be 2 digits")
        if not self.family_code.isdigit():
            raise ValueError("Family code must be numeric")
        if not self.member_code.isdigit():
            raise ValueError("Member code must be numeric")
    
    def __str__(self) -> str:
        return f"{self.client_code}-{self.family_code}-{self.member_code}"
    
    @classmethod
    def from_string(cls, code_str: str) -> 'ClientEmployeeCode':
        parts = code_str.split('-')
        if len(parts) != 3:
            raise ValueError(f"Invalid code format: {code_str}. Expected format: CLIENT-FAMILY-MEMBER")
        return cls(
            client_code=parts[0],
            family_code=parts[1],
            member_code=parts[2]
        )

@dataclass(frozen=True)
class EmploymentInfo:
    client_id: ClientId
    employee_code: ClientEmployeeCode
    role: str
    start_date: date
    status: WorkStatus
    department: str | None = None
    employee_id: str | None = None
    end_date: date | None = None
    def __post_init__(self):
        if self.end_date and self.end_date < self.start_date:
            raise ValueError("End date must be after start date")
    def is_active(self) -> bool:
        return self.status == WorkStatus.ACTIVE

@dataclass(frozen=True)
class StaffInfo:
    role: StaffRole
    client_id: ClientId
    department: str | None = None
    can_manage_clients: bool = False
    can_manage_services: bool = False
    can_view_reports: bool = False

@dataclass(frozen=True)
class DependentInfo:
    primary_employee_id: PersonId
    relationship: RelationType
    guardian_id: UserId | None = None
    def is_eligible(self) -> bool:
        return NotImplementedError("Dependent eligibility is not implemented")