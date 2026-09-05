from enum import Enum


class BaseStatus(str, Enum):
    ACTIVE = "Active"
    INACTIVE = "Inactive"
    PENDING = "Pending"
    ARCHIVED = "Archived"
    DELETED = "Deleted"


class SessionStatus(str, Enum):
    SCHEDULED = "Scheduled"
    RESCHEDULED = "Rescheduled"
    COMPLETED = "Completed"
    CANCELLED = "Cancelled"
    NO_SHOW = "No Show"


class SessionType(str, Enum):
    PHYSICAL = "Physical"
    ONLINE = "Online"


class SessionCategory(str, Enum):
    INDIVIDUAL = "Individual"
    GROUP = "Group"
    FAMILY = "Family"
    COUPLES = "Couples"


class ClientType(str, Enum):
    NEW = "New"
    REPEAT = "Repeat"


class SessionClinicalStatus(str, Enum):
    """Clinical continuation outcome recorded by the counsellor at session end.

    Distinct from SessionStatus (scheduling lifecycle).
    TO_BE_CONTINUED:  client returns for follow-up (xlsx: T).
    REFERRED:         client referred elsewhere (xlsx: R).
    COMPLETED:        case episode closed this session (xlsx: C).
    """

    TO_BE_CONTINUED = "ToBeContinued"
    REFERRED = "Referred"
    COMPLETED = "Completed"


class ServiceCategory(str, Enum):
    """Coarse grouping used by EAP programme caps and authorization rules."""

    SHORT_TERM_COUNSELLING = "ShortTermCounselling"
    CRISIS_INTERVENTION = "CrisisIntervention"
    SUBSTANCE_USE = "SubstanceUse"
    MANAGER_CONSULT = "ManagerConsult"
    WORK_LIFE_REFERRAL = "WorkLifeReferral"
    CISM_RESPONSE = "CISMResponse"
    WELLNESS_COACHING = "WellnessCoaching"
