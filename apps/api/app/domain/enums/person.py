from enum import Enum


class UserStatus(str, Enum):
    ACTIVE = "Active"
    SUSPENDED = "Suspended"
    BANNED = "Banned"
    TERMINATED = "Terminated"
    PENDING_VERIFICATION = "Pending Verification"
    INACTIVE = "Inactive"


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


class MemberRelation(str, Enum):
    """Relationship of an eligible member to the primary employee."""

    EMPLOYEE = "Employee"
    SPOUSE = "Spouse"
    CHILD = "Child"
    DOMESTIC_PARTNER = "DomesticPartner"
    DEPENDENT_OTHER = "DependentOther"


class MemberGender(str, Enum):
    """Optional demographic value. Restricted to Male/Female by product decision."""

    FEMALE = "Female"
    MALE = "Male"


class EligibilityStatus(str, Enum):
    """Lifecycle of an EAP-eligible member as supplied by the employer."""

    ACTIVE = "Active"
    SUSPENDED = "Suspended"
    TERMINATED = "Terminated"
    PENDING = "Pending"


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


class AuthProvider(str, Enum):
    """How a user authenticates. PASSWORD = tenant code + email + password; AZURE_AD = Microsoft SSO."""

    PASSWORD = "password"
    AZURE_AD = "azure_ad"
