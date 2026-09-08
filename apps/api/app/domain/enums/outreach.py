from enum import Enum


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
