from enum import Enum


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
