"""Domain events for the outreach bounded context."""

from dataclasses import dataclass

from app.domain.events.base import DomainEvent
from app.domain.value_objects.core import (
    CareCallbackCampaignId,
    ClientId,
    OutreachRecordId,
    ProviderId,
    SurveyCampaignId,
    SurveyResponseId,
    TenantId,
)


@dataclass(frozen=True)
class CareCallbackCampaignCreated(DomainEvent):
    """Raised when a Care Callback campaign is drafted."""

    campaign_id: "CareCallbackCampaignId"
    client_id: ClientId


@dataclass(frozen=True)
class CareCallbackCampaignActivated(DomainEvent):
    """Raised when a campaign is activated and outreach can begin."""

    campaign_id: "CareCallbackCampaignId"


@dataclass(frozen=True)
class CareCallbackCampaignCompleted(DomainEvent):
    """Raised when a campaign is closed; aggregated metrics are final."""

    campaign_id: "CareCallbackCampaignId"
    target_count: int
    completed_count: int


@dataclass(frozen=True)
class OutreachAssigned(DomainEvent):
    """Raised when an outreach record is routed to a counsellor."""

    outreach_id: "OutreachRecordId"
    counsellor_id: ProviderId


@dataclass(frozen=True)
class OutreachAttemptRecorded(DomainEvent):
    """Raised when a counsellor records an attempt to reach the person."""

    outreach_id: "OutreachRecordId"
    attempt_number: int


@dataclass(frozen=True)
class OutreachCompleted(DomainEvent):
    """Raised when an outreach is concluded (any terminal status)."""

    outreach_id: "OutreachRecordId"
    terminal_status: str


@dataclass(frozen=True)
class SurveyCampaignCreated(DomainEvent):
    campaign_id: "SurveyCampaignId"
    tenant_id: TenantId
    client_id: "ClientId"


@dataclass(frozen=True)
class SurveyCampaignActivated(DomainEvent):
    campaign_id: "SurveyCampaignId"


@dataclass(frozen=True)
class SurveyCampaignClosed(DomainEvent):
    campaign_id: "SurveyCampaignId"


@dataclass(frozen=True)
class SurveyResponseIngested(DomainEvent):
    response_id: "SurveyResponseId"
    campaign_id: "SurveyCampaignId"
    external_response_id: str
