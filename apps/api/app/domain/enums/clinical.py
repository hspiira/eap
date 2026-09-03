from enum import Enum


class ClientTier(str, Enum):
    """Joseph's A/B/C clustering for client engagement tiering.

    A — strategic / large account, full service mix.
    B — mid-tier, consultancy-extension candidates.
    C — long-tail / small account, lower-touch service model.
    """

    A = "A"
    B = "B"
    C = "C"


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


class StageOfChange(str, Enum):
    """Prochaska & DiClemente Transtheoretical Model stages."""

    PRECONTEMPLATION = "Precontemplation"
    CONTEMPLATION = "Contemplation"
    PREPARATION = "Preparation"
    ACTION = "Action"
    MAINTENANCE = "Maintenance"


class TriageRiskLevel(str, Enum):
    """Computed risk classification from a triage instrument response."""

    LOW = "Low"
    MODERATE = "Moderate"
    HIGH = "High"
    CRITICAL = "Critical"


class TriageInstrumentCode(str, Enum):
    """Versioned identifiers for the supported triage instruments.

    ``JOSEPH7`` — Joseph's 7-variable counsellor-callback screen.
    ``WOS5`` — 5-item Work Outcome Scale (pre/post case).
    ``PHQ9`` — 9-item Patient Health Questionnaire; item-9 > 0 triggers crisis.
    ``GAD7`` — 7-item Generalized Anxiety Disorder screen.
    ``CSSRS`` — Columbia Suicide Severity Rating Scale (brief).
    ``AUDIT_C`` — 3-item alcohol-use disorders screener.
    ``DAST10`` — 10-item Drug Abuse Screening Test.
    ``WHO5`` — 5-item WHO wellbeing index.
    ``K10`` — Kessler 10 psychological distress.
    ``WSAS`` — Work and Social Adjustment Scale.
    ``DASS21`` — Depression, Anxiety, Stress 21-item scale.
    ``PCL5`` — PTSD Checklist for DSM-5 (post-CISM).
    """

    JOSEPH7 = "JOSEPH7"
    WOS5 = "WOS5"
    PHQ9 = "PHQ9"
    GAD7 = "GAD7"
    CSSRS = "CSSRS"
    AUDIT_C = "AUDIT_C"
    DAST10 = "DAST10"
    WHO5 = "WHO5"
    K10 = "K10"
    WSAS = "WSAS"
    DASS21 = "DASS21"
    PCL5 = "PCL5"
