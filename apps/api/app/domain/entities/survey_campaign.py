"""Survey campaign aggregate (Phase 3 #D-Survey / SAD §5.2.7).

A SurveyCampaign owns the configuration and lifecycle of an external-form
collection (Google Forms first; Typeform/MS Forms via the same shape). The
campaign carries a tenant-scoped HMAC ``webhook_secret`` so the public
ingestion endpoint can verify each delivery without an authenticated user.
"""

from dataclasses import dataclass, field
from datetime import date, datetime

from app.domain.enums import SurveyCampaignStatus, SurveySource
from app.domain.events import (
    DomainEvent,
    SurveyCampaignActivated,
    SurveyCampaignClosed,
    SurveyCampaignCreated,
)
from app.domain.exceptions import DomainError, InvalidStateError
from app.domain.value_objects.core import (
    ClientId,
    SurveyCampaignId,
    TenantId,
    UserId,
)
from app.shared.utils.datetime import utc_now


@dataclass
class SurveyCampaign:
    """Configuration + lifecycle for one external survey collection."""

    id: SurveyCampaignId
    tenant_id: TenantId
    client_id: ClientId
    name: str
    source: SurveySource
    external_form_id: str
    webhook_secret: str
    status: SurveyCampaignStatus
    created_by: UserId
    created_at: datetime
    updated_at: datetime
    period_start: date | None = None
    period_end: date | None = None
    anonymous: bool = True
    activated_at: datetime | None = None
    closed_at: datetime | None = None
    response_count: int = 0
    events: list[DomainEvent] = field(default_factory=list[DomainEvent])

    def __post_init__(self) -> None:
        if not self.name:
            raise DomainError("SurveyCampaign requires a name")
        if not self.external_form_id:
            raise DomainError("SurveyCampaign requires external_form_id")
        if len(self.webhook_secret) < 32:
            raise DomainError("webhook_secret must be at least 32 chars")
        if self.period_start and self.period_end and self.period_end < self.period_start:
            raise DomainError("period_end must be on or after period_start")
        if self.response_count < 0:
            raise DomainError("response_count cannot be negative")
        if self.created_at == self.updated_at and not self.events:
            self.events.append(
                SurveyCampaignCreated(
                    occurred_at=self.created_at,
                    campaign_id=self.id,
                    tenant_id=self.tenant_id,
                    client_id=self.client_id,
                )
            )

    def activate(self, now: datetime | None = None) -> None:
        if self.status != SurveyCampaignStatus.DRAFT:
            raise InvalidStateError(
                f"Cannot activate survey campaign in status {self.status.value}"
            )
        now = now or utc_now()
        self.status = SurveyCampaignStatus.ACTIVE
        self.activated_at = now
        self.updated_at = now
        self.events.append(SurveyCampaignActivated(occurred_at=now, campaign_id=self.id))

    def close(self, now: datetime | None = None) -> None:
        if self.status != SurveyCampaignStatus.ACTIVE:
            raise InvalidStateError(f"Cannot close survey campaign in status {self.status.value}")
        now = now or utc_now()
        self.status = SurveyCampaignStatus.CLOSED
        self.closed_at = now
        self.updated_at = now
        self.events.append(SurveyCampaignClosed(occurred_at=now, campaign_id=self.id))

    def is_accepting_responses(self) -> bool:
        return self.status == SurveyCampaignStatus.ACTIVE

    def increment_response_count(self, now: datetime | None = None) -> None:
        self.response_count += 1
        self.updated_at = now or utc_now()
