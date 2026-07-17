"""
Domain value objects for the Evexía core domain.

Value objects are immutable types that represent domain concepts with self-validation.
They have no identity, only value.
"""

import decimal
import re
from dataclasses import dataclass
from datetime import date, datetime

from app.domain.enums import (
    AccreditationStatus,
    PanelStatus,
    ProviderTier,
    RelationType,
    StaffRole,
    UgandaRegion,
    WorkStatus,
)
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
                + "(e.g., 'acme', 'acme-corp', 'abc123')"
            )

# === Identity Value Objects ===
#
# Each entity has its own ID subclass so the type checker can flag
# cross-type misuse (e.g. passing a PersonId where a UserId is expected).
# Runtime behaviour is identical to the base `Id`: same string validation,
# same equality semantics. Subclasses exist purely for nominal typing.


@dataclass(frozen=True)
class Id:
    """Base identifier value object.

    Attributes:
    - 1..25 characters
    - immutable
    """
    value: str

    def __post_init__(self):
        if not self.value or len(self.value) > 25:
            raise ValueError("ID must be 1..25 characters")


@dataclass(frozen=True)
class TenantId(Id):
    pass


@dataclass(frozen=True)
class PersonId(Id):
    pass


@dataclass(frozen=True)
class ContractId(Id):
    pass


@dataclass(frozen=True)
class ServiceId(Id):
    pass


@dataclass(frozen=True)
class SessionId(Id):
    pass


@dataclass(frozen=True)
class UserId(Id):
    pass


@dataclass(frozen=True)
class ClientId(Id):
    pass


@dataclass(frozen=True)
class IndustryId(Id):
    pass


@dataclass(frozen=True)
class AuditLogId(Id):
    pass


@dataclass(frozen=True)
class EntityChangeId(Id):
    pass


@dataclass(frozen=True)
class DocumentId(Id):
    pass


@dataclass(frozen=True)
class KPIId(Id):
    pass


@dataclass(frozen=True)
class KPIAssignmentId(Id):
    pass


@dataclass(frozen=True)
class ClientTagId(Id):
    pass


@dataclass(frozen=True)
class ContactId(Id):
    pass


@dataclass(frozen=True)
class ActivityId(Id):
    pass


@dataclass(frozen=True)
class ServiceAssignmentId(Id):
    pass


@dataclass(frozen=True)
class CriticalIncidentId(Id):
    pass


@dataclass(frozen=True)
class NonCompeteClauseId(Id):
    pass


@dataclass(frozen=True)
class ReportTemplateId(Id):
    pass


@dataclass(frozen=True)
class ReportRunId(Id):
    pass


@dataclass(frozen=True)
class UtilisationEventId(Id):
    pass


@dataclass(frozen=True)
class CareCallbackCampaignId(Id):
    pass


@dataclass(frozen=True)
class OutreachRecordId(Id):
    pass


@dataclass(frozen=True)
class TriageResponseId(Id):
    pass


@dataclass(frozen=True)
class SurveyCampaignId(Id):
    pass


@dataclass(frozen=True)
class SurveyResponseId(Id):
    pass


@dataclass(frozen=True)
class EngagementId(Id):
    pass


@dataclass(frozen=True)
class DeliverableId(Id):
    pass


@dataclass(frozen=True)
class HoursLogEntryId(Id):
    pass


@dataclass(frozen=True)
class DSARRequestId(Id):
    pass


@dataclass(frozen=True)
class BenchmarkConsentId(Id):
    pass


@dataclass(frozen=True)
class EligibleMemberId(Id):
    pass


@dataclass(frozen=True)
class ClinicalSubjectId(Id):
    pass


@dataclass(frozen=True)
class CaseId(Id):
    pass


@dataclass(frozen=True)
class AuthorizationId(Id):
    pass


@dataclass(frozen=True)
class EAPProgrammeId(Id):
    pass


@dataclass(frozen=True)
class ClinicalNoteId(Id):
    pass


@dataclass(frozen=True)
class NoteAmendmentId(Id):
    pass


@dataclass(frozen=True)
class CrisisContactId(Id):
    pass


@dataclass(frozen=True)
class RiskAssessmentId(Id):
    pass


@dataclass(frozen=True)
class SafetyPlanId(Id):
    pass


@dataclass(frozen=True)
class MandatoryReportId(Id):
    pass


@dataclass(frozen=True)
class CaringContactId(Id):
    pass


@dataclass(frozen=True)
class ManagerConsultId(Id):
    pass


@dataclass(frozen=True)
class WorkLifeReferralId(Id):
    pass


@dataclass(frozen=True)
class WorkLifeProviderId(Id):
    pass


@dataclass(frozen=True)
class TrainingEnrolmentId(Id):
    pass


@dataclass(frozen=True)
class OutcomeMeasureId(Id):
    pass


@dataclass(frozen=True)
class FitnessForDutyId(Id):
    pass


@dataclass(frozen=True)
class ReturnToWorkPlanId(Id):
    pass


@dataclass(frozen=True)
class ConsentId(Id):
    pass


@dataclass(frozen=True)
class DataSharingRegisterEntryId(Id):
    pass


@dataclass(frozen=True)
class DPOContactId(Id):
    pass

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
class ProviderProfile:
    """Panel-level metadata about a service provider (Joseph's framework)."""

    tier: ProviderTier
    region: UgandaRegion
    accreditation_status: AccreditationStatus
    panel_status: PanelStatus = PanelStatus.ACTIVE
    accreditation_authority: str | None = None
    accreditation_expiry: date | None = None
    specialties: tuple[str, ...] = ()
    bio: str | None = None

    def is_panel_eligible(self) -> bool:
        """Whether the provider can currently take new assignments."""
        if self.panel_status != PanelStatus.ACTIVE:
            return False
        if self.accreditation_status != AccreditationStatus.ACCREDITED:
            return False
        if self.accreditation_expiry is not None and self.accreditation_expiry < utc_now().date():
            return False
        return True

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

    def __post_init__(self):
        if not self.primary_employee_id:
            raise ValueError("DependentInfo requires primary_employee_id")

    def is_eligible(self) -> bool:
        """Intrinsic eligibility derived from the dependent's own data.

        Cross-aggregate eligibility (the primary employee's active status)
        is composed at PersonEntity.is_eligible_for_services. Here we check
        only what this VO can know: the relationship type is one we accept,
        and the linkage to a primary employee is present.
        """
        return self.relationship in {
            RelationType.SPOUSE,
            RelationType.CHILD,
            RelationType.PARENT,
            RelationType.SIBLING,
            RelationType.GRANDPARENT,
            RelationType.GUARDIAN,
        }