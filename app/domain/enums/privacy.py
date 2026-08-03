from enum import Enum


class DSARRequestType(str, Enum):
    """Subject access request type (SAD §6.6 / §8.4)."""

    EXPORT = "Export"
    ERASURE = "Erasure"


class DSARRequestStatus(str, Enum):
    """DSAR fulfilment lifecycle."""

    REQUESTED = "Requested"
    PROCESSING = "Processing"
    COMPLETED = "Completed"
    FAILED = "Failed"
    CANCELLED = "Cancelled"


class RetentionDataClass(str, Enum):
    """Data classes for per-class retention policies (SAD §6.6)."""

    SESSIONS = "Sessions"
    TRIAGE = "Triage"
    SURVEY = "Survey"
    AUDIT = "Audit"
    ENGAGEMENTS = "Engagements"
    OUTREACH = "Outreach"


class ConsentStatus(str, Enum):
    PENDING = "Pending"
    ACTIVE = "Active"
    EXPIRED = "Expired"
    REVOKED = "Revoked"


class ConsentScope(str, Enum):
    """Granular disclosure scope for a Release-of-Information consent."""

    ATTENDANCE_ONLY = "AttendanceOnly"
    DIAGNOSIS = "Diagnosis"
    RISK_ONLY = "RiskOnly"
    FULL_CASE_DETAIL = "FullCaseDetail"


class ConsentPurpose(str, Enum):
    EMPLOYER_MANDATORY_REFERRAL = "EmployerMandatoryReferral"
    SPECIALIST_HANDOFF = "SpecialistHandoff"
    FAMILY_INCLUSION = "FamilyInclusion"
    COURT_ORDER = "CourtOrder"
    INSURANCE = "Insurance"
    RESEARCH_DEIDENTIFIED = "ResearchDeIdentified"
    OTHER = "Other"
