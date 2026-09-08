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


class SessionAttendance(str, Enum):
    """Who a session was delivered to.

    COMPANY_WIDE covers a health talk or site visit: a real session delivered to
    a client with no individual to name. It is not the same as not knowing who
    attended. The source extract holds 569 rows marked Staff or Dependant with
    no member id, and those are unresolved identities that stay staged rather
    than becoming member-less sessions. Keeping the two apart is what lets
    validation require a headcount here and a member there.
    """

    INDIVIDUAL = "Individual"
    COMPANY_WIDE = "CompanyWide"


class ClientType(str, Enum):
    NEW = "New"
    REPEAT = "Repeat"


class SessionClinicalStatus(str, Enum):
    """Clinical continuation outcome recorded by the counsellor at session end.

    Distinct from SessionStatus (scheduling lifecycle).
    TO_BE_CONTINUED:  client returns for follow-up (xlsx: T).
    REFERRED:         client referred elsewhere (xlsx: R).
    COMPLETED:        case episode closed this session (xlsx: C).
    TERMINATED:       engagement ended without completing.
    """

    TO_BE_CONTINUED = "ToBeContinued"
    REFERRED = "Referred"
    COMPLETED = "Completed"
    TERMINATED = "Terminated"


class SessionDeliveryContext(str, Enum):
    """How the practitioner delivered, or will deliver, this session.

    UNKNOWN describes a historical record whose source carries no evidence of
    the arrangement. It is never accepted on a live booking; inferring direct
    delivery from a missing value would assert something the source does not say.
    """

    DIRECT = "Direct"
    ORGANISATION = "Organisation"
    UNKNOWN = "Unknown"
