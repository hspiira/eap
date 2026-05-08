"""Enumerations for the application."""

from enum import Enum

class TenantStatus(str, Enum):
    ACTIVE = "Active"
    SUSPENDED = "Suspended"
    TERMINATED = "Terminated"
    ARCHIVED = "Archived"

class UserStatus(str, Enum):
    ACTIVE = "Active"
    SUSPENDED = "Suspended"
    BANNED = "Banned"
    TERMINATED = "Terminated"
    PENDING_VERIFICATION = "Pending Verification"
    INACTIVE = "Inactive"


class TenantRole(str, Enum):
    """Role within a tenant for RBAC. ADMIN can manage tenant and users."""
    ADMIN = "Admin"
    USER = "User"
    VIEWER = "Viewer"

class BaseStatus(str, Enum):
    ACTIVE = "Active"
    INACTIVE = "Inactive"
    PENDING = "Pending"
    ARCHIVED = "Archived"
    DELETED = "Deleted"

class PersonType(str, Enum):
    PLATFORM_STAFF = "PlatformStaff"
    CLIENT_EMPLOYEE = "ClientEmployee"
    DEPENDENT = "Dependent"
    SERVICE_PROVIDER = "ServiceProvider"

class WorkStatus(str, Enum):
    ACTIVE = "Active"
    INACTIVE = "Inactive"
    ON_LEAVE = "On Leave"
    TERMINATED = "Terminated"
    SUSPENDED = "Suspended"
    RESIGNED = "Resigned"

class StaffRole(str, Enum):
    ADMIN = "Admin"
    MANAGER = "Manager"
    STAFF = "Staff"
    VOLUNTEER = "Volunteer"

class RelationType(str, Enum):
    CHILD = "Child"
    SPOUSE = "Spouse"
    PARENT = "Parent"
    SIBLING = "Sibling"
    GRANDPARENT = "Grandparent"
    GUARDIAN = "Guardian"
    OTHER = "Other"

class ContractStatus(str, Enum):
    ACTIVE = "Active"
    EXPIRED = "Expired"
    TERMINATED = "Terminated"
    RENEWED = "Renewed"
    PENDING = "Pending"
    DRAFT = "Draft"

class PaymentStatus(str, Enum):
    PENDING = "Pending"
    PAID = "Paid"
    OVERDUE = "Overdue"
    CANCELLED = "Cancelled"
    REFUNDED = "Refunded"

class PaymentFrequency(str, Enum):
    WEEKLY = "Weekly"
    MONTHLY = "Monthly"
    QUARTERLY = "Quarterly"
    ANNUALLY = "Annually"

class SessionStatus(str, Enum):
    SCHEDULED = "Scheduled"
    RESCHEDULED = "Rescheduled"
    COMPLETED = "Completed"
    CANCELLED = "Cancelled"
    NO_SHOW = "No Show"


class ClientTier(str, Enum):
    """Joseph's A/B/C clustering for client engagement tiering.

    A — strategic / large account, full service mix.
    B — mid-tier, consultancy-extension candidates.
    C — long-tail / small account, lower-touch service model.
    """

    A = "A"
    B = "B"
    C = "C"


class CriticalIncidentSeverity(str, Enum):
    """Operational severity used to triage critical-incident response."""

    LOW = "Low"
    MEDIUM = "Medium"
    HIGH = "High"
    CATASTROPHIC = "Catastrophic"


class CriticalIncidentStatus(str, Enum):
    """Lifecycle of an incident response."""

    OPEN = "Open"
    IN_RESPONSE = "InResponse"
    CLOSED = "Closed"


class CriticalIncidentPhase(str, Enum):
    """Mitchell-Everly CISM phases tracked on the response timeline (SAD §2.6)."""

    DEMOBILISATION = "Demobilisation"
    DEFUSING = "Defusing"
    DEBRIEFING = "Debriefing"
    ONE_ON_ONE = "OneOnOne"
    FAMILY = "FamilyCISM"
    PASTORAL = "Pastoral"
    FOLLOW_UP = "FollowUp"

class SubscriptionTier(str, Enum):
    FREE = "Free"
    BASIC = "Basic"
    PROFESSIONAL = "Professional"
    ENTERPRISE = "Enterprise"

class Language(str, Enum):
    ENGLISH = "en"
    SPANISH = "es"
    FRENCH = "fr"
    GERMAN = "de"
    ITALIAN = "it"
    PORTUGUESE = "pt"
    CHINESE = "zh"
    JAPANESE = "ja"
    KOREAN = "ko"

class ContactMethod(str, Enum):
    EMAIL = "email"
    PHONE = "phone"
    SMS = "sms"
    WHATSAPP = "whatsapp"
    WECHAT = "wechat"

class AuditActionType(str, Enum):
    """Types of actions that can be audited.
    
    Note: LIST and VIEW actions are subject to configurable filtering/sampling
    to prevent audit log bloat. Critical actions (CREATE, UPDATE, DELETE, etc.)
    are always logged. See AUDIT_SAMPLE_RATE, AUDIT_ALWAYS_LOG_RESOURCES, and
    AUDIT_SKIP_RESOURCES environment variables for configuration.
    """
    CREATE = "CREATE"
    UPDATE = "UPDATE"
    DELETE = "DELETE"
    LOGIN = "LOGIN"
    LOGOUT = "LOGOUT"
    APPROVE = "APPROVE"
    REJECT = "REJECT"
    LIST = "LIST"  # Subject to filtering/sampling
    VIEW = "VIEW"  # Subject to filtering/sampling
    EXPORT = "EXPORT"
    IMPORT = "IMPORT"

class DocumentType(str, Enum):
    """Types of documents in the system."""
    CONTRACT = "Contract"
    CERTIFICATION = "Certification"
    KPI_REPORT = "KPI Report"
    FEEDBACK_SUMMARY = "Feedback Summary"
    BILLING_REPORT = "Billing Report"
    UTILIZATION_REPORT = "Utilization Report"
    OTHER = "Other"

class DocumentStatus(str, Enum):
    """Status of a document."""
    DRAFT = "Draft"
    PUBLISHED = "Published"
    ARCHIVED = "Archived"
    EXPIRED = "Expired"

class KPICategory(str, Enum):
    """Categories for KPIs."""
    UTILIZATION = "Utilization"
    SATISFACTION = "Satisfaction"
    OUTCOME = "Outcome"
    OPERATIONAL = "Operational"

class KPIMeasurementUnit(str, Enum):
    """Units for KPI measurements."""
    PERCENTAGE = "Percentage"
    COUNT = "Count"
    RATE = "Rate"
    SCORE = "Score"
    TIME = "Time"
    CURRENCY = "Currency"
