from enum import Enum


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
