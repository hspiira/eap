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


class ProviderTier(str, Enum):
    """Provider panel tier — drives routing and rate cards (Joseph's framework)."""

    T1 = "T1"
    T2 = "T2"
    T3 = "T3"


class UgandaRegion(str, Enum):
    """The 8 empanelment regions used for provider geo-distribution."""

    CENTRAL = "Central"
    KAMPALA_METRO = "KampalaMetro"
    EASTERN = "Eastern"
    NORTHERN = "Northern"
    WEST_NILE = "WestNile"
    WESTERN = "Western"
    SOUTH_WESTERN = "SouthWestern"
    KARAMOJA = "Karamoja"


class AccreditationStatus(str, Enum):
    """Where the provider sits in the accreditation pipeline."""

    PENDING = "Pending"
    ACCREDITED = "Accredited"
    LAPSED = "Lapsed"
    SUSPENDED = "Suspended"
    REJECTED = "Rejected"


class PanelStatus(str, Enum):
    """Whether the provider is currently on the active panel."""

    ACTIVE = "Active"
    SUSPENDED = "Suspended"
    REMOVED = "Removed"


class NonCompeteStatus(str, Enum):
    """Lifecycle of a non-compete clause."""

    DRAFT = "Draft"
    ACTIVE = "Active"
    REVOKED = "Revoked"
    EXPIRED = "Expired"


class ReportQueryType(str, Enum):
    """Library of canned report queries (SAD §5.2.10).

    Each value maps to a single :class:`~app.application.services.report_query_runner.QueryRunner`
    method. New queries are added by extending the enum and adding a runner;
    templates reference them by enum value.
    """

    SESSIONS_BY_MONTH = "sessions_by_month"
    DIAGNOSIS_PREVALENCE = "diagnosis_prevalence"
    CONTRACT_UTILISATION = "contract_utilisation"
    CARE_CALLBACK_OUTCOMES = "care_callback_outcomes"
    SATISFACTION_DISTRIBUTION = "satisfaction_distribution"


class ReportRunStatus(str, Enum):
    """Lifecycle of a single report execution."""

    PENDING = "Pending"
    RUNNING = "Running"
    COMPLETED = "Completed"
    FAILED = "Failed"


class PricingModel(str, Enum):
    """Joseph's five contract pricing strategies (SAD §5.2.3 / Meeting §3).

    RETAINER — fixed periodic fee (e.g. monthly).
    FRAMEWORK — pre-paid deposit drawn down per session.
    FEE_FOR_SERVICE — pay per session at a rate card.
    ADMIN_UTILISATION — admin-fee floor + per-session usage charges above the floor.
    VALUE_ADD — bundled into a broader Minet relationship (no per-EAP invoice).
    """

    RETAINER = "Retainer"
    FRAMEWORK = "Framework"
    FEE_FOR_SERVICE = "FeeForService"
    ADMIN_UTILISATION = "AdminUtilisation"
    VALUE_ADD = "ValueAdd"


class UtilisationEventType(str, Enum):
    """Kinds of billable activity tracked against a contract."""

    SESSION_DELIVERED = "SessionDelivered"
    CARE_CALLBACK = "CareCallback"
    SURVEY = "Survey"
    INCIDENT_RESPONSE = "IncidentResponse"
    CONSULTANCY_HOURS = "ConsultancyHours"


class CareCallbackCampaignStatus(str, Enum):
    """Lifecycle of a Counsellor-Initiated Care Call campaign."""

    DRAFT = "Draft"
    ACTIVE = "Active"
    COMPLETED = "Completed"
    ARCHIVED = "Archived"


class OutreachStatus(str, Enum):
    """Per-person outreach lifecycle within a campaign."""

    PENDING = "Pending"
    ASSIGNED = "Assigned"
    CONTACTED = "Contacted"
    COMPLETED = "Completed"
    UNREACHABLE = "Unreachable"
    DECLINED = "Declined"
    ESCALATED = "Escalated"


class TriageRiskLevel(str, Enum):
    """Computed risk classification from a triage instrument response."""

    LOW = "Low"
    MODERATE = "Moderate"
    HIGH = "High"
    CRITICAL = "Critical"


class TriageInstrumentCode(str, Enum):
    """Versioned identifiers for the supported triage instruments.

    ``JOSEPH7`` — Joseph's 7-variable counsellor-callback screen (SAD §B.4).
    ``WOS5`` — 5-item Work Outcome Scale (SAD §2.3.1; pre/post case).
    ``PHQ9`` — 9-item Patient Health Questionnaire; item-9 > 0 triggers crisis.
    """

    JOSEPH7 = "JOSEPH7"
    WOS5 = "WOS5"
    PHQ9 = "PHQ9"


class StageOfChange(str, Enum):
    """Prochaska & DiClemente Transtheoretical Model stages."""

    PRECONTEMPLATION = "Precontemplation"
    CONTEMPLATION = "Contemplation"
    PREPARATION = "Preparation"
    ACTION = "Action"
    MAINTENANCE = "Maintenance"


class SurveyCampaignStatus(str, Enum):
    """Lifecycle state of a survey campaign."""

    DRAFT = "Draft"
    ACTIVE = "Active"
    CLOSED = "Closed"


class SurveySource(str, Enum):
    """Upstream survey provider (extensible)."""

    GOOGLE_FORMS = "GoogleForms"
    TYPEFORM = "Typeform"
    MICROSOFT_FORMS = "MicrosoftForms"


class EngagementStatus(str, Enum):
    """Cluster B consultancy engagement lifecycle (SAD §5.2.8)."""

    DRAFT = "Draft"
    ACTIVE = "Active"
    DELIVERED = "Delivered"
    INVOICED = "Invoiced"
    CLOSED = "Closed"


class DeliverableStatus(str, Enum):
    """Per-deliverable lifecycle within an Engagement."""

    PENDING = "Pending"
    IN_PROGRESS = "InProgress"
    DELIVERED = "Delivered"
    ACCEPTED = "Accepted"


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


class BenchmarkScope(str, Enum):
    """Metric families a tenant can opt into for cross-tenant benchmarking."""

    SESSION_VOLUME = "SessionVolume"
    UTILISATION_RATES = "UtilisationRates"
    SATISFACTION = "Satisfaction"
    CARE_CALLBACK_OUTCOMES = "CareCallbackOutcomes"


class TenantConsentStatus(str, Enum):
    ACTIVE = "Active"
    WITHDRAWN = "Withdrawn"


class EligibilityStatus(str, Enum):
    """Lifecycle of an EAP-eligible member as supplied by the employer."""

    ACTIVE = "Active"
    SUSPENDED = "Suspended"
    TERMINATED = "Terminated"
    PENDING = "Pending"


class MemberRelation(str, Enum):
    """Relationship of an eligible member to the primary employee."""

    EMPLOYEE = "Employee"
    SPOUSE = "Spouse"
    CHILD = "Child"
    DOMESTIC_PARTNER = "DomesticPartner"
    DEPENDENT_OTHER = "DependentOther"


class AccessScope(str, Enum):
    """Bounded-context split between the employer-facing and clinical surfaces.

    A token's scope determines which routes it may reach. The clinical scope is
    a strict superset of nothing: a clinical user has zero employer-side
    privilege and vice versa, even within the same tenant.
    """

    EMPLOYER_PORTAL = "EmployerPortal"
    CLINICAL = "Clinical"
    PLATFORM_ADMIN = "PlatformAdmin"


class CaseStatus(str, Enum):
    """Lifecycle of a clinical case."""

    INTAKE = "Intake"
    ASSESSMENT = "Assessment"
    ACTIVE = "Active"
    CLOSED = "Closed"
    REFERRED_OUT = "ReferredOut"
    NO_SHOW_CLOSED = "NoShowClosed"


class CaseReferralSource(str, Enum):
    """Origin of a case — drives downstream disclosure and reporting rules."""

    SELF = "Self"
    INFORMAL_MANAGER = "InformalManager"
    FORMAL_MANDATORY = "FormalMandatory"
    HR = "HR"
    CISM_FOLLOWUP = "CISMFollowUp"
    EMPLOYER_PROACTIVE = "EmployerProactive"


class PresentingProblem(str, Enum):
    """Top-level category of the presenting concern at intake."""

    MENTAL_HEALTH = "MentalHealth"
    STRESS = "Stress"
    RELATIONSHIP = "Relationship"
    WORK = "Work"
    FINANCIAL = "Financial"
    SUBSTANCE = "Substance"
    BEREAVEMENT = "Bereavement"
    TRAUMA = "Trauma"
    FAMILY_CHILD = "FamilyChild"
    OTHER = "Other"


class CaseClosureReason(str, Enum):
    """Why a case was closed; recorded at the closure transition."""

    GOALS_MET = "GoalsMet"
    CLIENT_DISCONTINUED = "ClientDiscontinued"
    REFERRED_OUT = "ReferredOut"
    NO_SHOW = "NoShow"
    SESSION_CAP_REACHED = "SessionCapReached"
    INELIGIBLE = "Ineligible"
    OTHER = "Other"


class ClinicalNoteType(str, Enum):
    """Shape of a clinical note record."""

    DAP = "DAP"
    SOAP = "SOAP"
    PHONE_CONTACT = "PhoneContact"
    CRISIS_CONTACT = "CrisisContact"
    CLOSURE_SUMMARY = "ClosureSummary"
    SUPERVISION = "Supervision"


class AuthorizationStatus(str, Enum):
    """State of a per-case session-cap authorization."""

    ACTIVE = "Active"
    EXTENSION_REQUESTED = "ExtensionRequested"
    EXTENDED = "Extended"
    EXHAUSTED = "Exhausted"
    EXPIRED = "Expired"
    CLOSED = "Closed"


class ServiceCategory(str, Enum):
    """Coarse grouping used by EAP programme caps and authorization rules."""

    SHORT_TERM_COUNSELLING = "ShortTermCounselling"
    CRISIS_INTERVENTION = "CrisisIntervention"
    SUBSTANCE_USE = "SubstanceUse"
    MANAGER_CONSULT = "ManagerConsult"
    WORK_LIFE_REFERRAL = "WorkLifeReferral"
    CISM_RESPONSE = "CISMResponse"
    WELLNESS_COACHING = "WellnessCoaching"


class CrisisCallerRelation(str, Enum):
    SELF = "Self"
    FAMILY = "Family"
    MANAGER = "Manager"
    COLLEAGUE = "Colleague"
    ANONYMOUS = "Anonymous"


class CrisisWarmHandoff(str, Enum):
    NONE = "None"
    MOBILE_CRISIS_TEAM = "MobileCrisisTeam"
    EMERGENCY_DEPARTMENT = "EmergencyDepartment"
    ON_CALL_CLINICIAN = "OnCallClinician"
    NATIONAL_HOTLINE = "NationalHotline"
    LAW_ENFORCEMENT = "LawEnforcement"


class CrisisContactOutcome(str, Enum):
    INFORMATION_ONLY = "InformationOnly"
    BOOKED_APPOINTMENT = "BookedAppointment"
    REFERRED_INTERNAL = "ReferredInternal"
    REFERRED_EXTERNAL = "ReferredExternal"
    EMERGENCY_DISPATCHED = "EmergencyDispatched"
    CALLER_DISCONNECTED = "CallerDisconnected"


class SafetyPlanStatus(str, Enum):
    DRAFT = "Draft"
    ACTIVE = "Active"
    REVIEWED = "Reviewed"
    SUPERSEDED = "Superseded"


class MandatoryReportType(str, Enum):
    TARASOFF = "Tarasoff"
    CHILD_ABUSE = "ChildAbuse"
    VULNERABLE_ADULT = "VulnerableAdult"
    SUICIDE_ATTEMPT = "SuicideAttempt"


class CaringContactChannel(str, Enum):
    CALL = "Call"
    SMS = "SMS"
    EMAIL = "Email"
    POSTCARD = "Postcard"


class CaringContactOutcome(str, Enum):
    PENDING = "Pending"
    COMPLETED = "Completed"
    NO_RESPONSE = "NoResponse"
    REFUSED = "Refused"
    LOST_CONTACT = "LostContact"


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
