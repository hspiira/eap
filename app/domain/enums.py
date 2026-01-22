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
    PENDING_VERIFICATION = "Pending Verification"
    INACTIVE = "Inactive"

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
    """Types of actions that can be audited."""
    CREATE = "CREATE"
    UPDATE = "UPDATE"
    DELETE = "DELETE"
    LOGIN = "LOGIN"
    LOGOUT = "LOGOUT"
    APPROVE = "APPROVE"
    REJECT = "REJECT"
    LIST = "LIST"
    VIEW = "VIEW"
    EXPORT = "EXPORT"
    IMPORT = "IMPORT"
