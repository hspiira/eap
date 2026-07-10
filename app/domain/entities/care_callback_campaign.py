"""Care Callback campaign aggregate (Phase 3 #D-CareCallback / SAD §5.2.6).

Joseph's flagship product. A campaign is a time-boxed wave of proactive
outreach to a defined target population at one client; the system samples,
assigns counsellors, captures triage, and aggregates outcomes.
"""

from dataclasses import dataclass, field
from datetime import date, datetime

from app.domain.enums import CareCallbackCampaignStatus
from app.domain.events import (
    CareCallbackCampaignActivated,
    CareCallbackCampaignCompleted,
    CareCallbackCampaignCreated,
    DomainEvent,
)
from app.domain.exceptions import DomainError, InvalidStateError
from app.domain.value_objects.core import (
    CareCallbackCampaignId,
    ClientId,
    PersonId,
    TenantId,
    UserId,
)
from app.shared.utils.datetime import utc_now


@dataclass
class CareCallbackCampaign:
    """A campaign that orchestrates outreach to a target population."""

    id: CareCallbackCampaignId
    tenant_id: TenantId
    client_id: ClientId
    name: str
    period_start: date
    period_end: date
    target_count: int
    counsellor_pool: tuple[PersonId, ...]
    status: CareCallbackCampaignStatus
    created_by: UserId
    created_at: datetime
    updated_at: datetime
    sampling_notes: str | None = None
    completed_at: datetime | None = None
    completed_count: int = 0
    activated_at: datetime | None = None
    events: list[DomainEvent] = field(default_factory=list[DomainEvent])

    def __post_init__(self) -> None:
        if not self.name:
            raise DomainError("Campaign requires a name")
        if self.period_end < self.period_start:
            raise DomainError("Campaign period_end must be on or after period_start")
        if self.target_count < 0:
            raise DomainError("Campaign target_count cannot be negative")
        if self.completed_count < 0:
            raise DomainError("completed_count cannot be negative")
        if self.created_at == self.updated_at and not self.events:
            self.events.append(
                CareCallbackCampaignCreated(
                    occurred_at=self.created_at,
                    campaign_id=self.id,
                    client_id=self.client_id,
                )
            )

    def activate(self, now: datetime | None = None) -> None:
        """Open the campaign for outreach work."""
        if self.status != CareCallbackCampaignStatus.DRAFT:
            raise InvalidStateError(
                f"Cannot activate campaign in status {self.status.value}"
            )
        if not self.counsellor_pool:
            raise DomainError("Cannot activate a campaign with an empty counsellor pool")
        now = now or utc_now()
        self.status = CareCallbackCampaignStatus.ACTIVE
        self.activated_at = now
        self.updated_at = now
        self.events.append(
            CareCallbackCampaignActivated(occurred_at=now, campaign_id=self.id)
        )

    def complete(self, now: datetime | None = None) -> None:
        """Close the campaign; aggregated metrics are final after this point."""
        if self.status != CareCallbackCampaignStatus.ACTIVE:
            raise InvalidStateError(
                f"Cannot complete campaign in status {self.status.value}"
            )
        now = now or utc_now()
        self.status = CareCallbackCampaignStatus.COMPLETED
        self.completed_at = now
        self.updated_at = now
        self.events.append(
            CareCallbackCampaignCompleted(
                occurred_at=now,
                campaign_id=self.id,
                target_count=self.target_count,
                completed_count=self.completed_count,
            )
        )

    def archive(self, now: datetime | None = None) -> None:
        """Archive a draft or completed campaign."""
        if self.status == CareCallbackCampaignStatus.ARCHIVED:
            raise InvalidStateError("Campaign is already archived")
        if self.status == CareCallbackCampaignStatus.ACTIVE:
            raise InvalidStateError("Complete an active campaign before archiving it")
        now = now or utc_now()
        self.status = CareCallbackCampaignStatus.ARCHIVED
        self.updated_at = now

    def update_counsellor_pool(self, pool: tuple[PersonId, ...]) -> None:
        """Replace the counsellor pool for the campaign."""
        if self.status not in {
            CareCallbackCampaignStatus.DRAFT,
            CareCallbackCampaignStatus.ACTIVE,
        }:
            raise InvalidStateError(
                f"Cannot change counsellor pool for {self.status.value} campaign"
            )
        self.counsellor_pool = pool
        self.updated_at = utc_now()

    def increment_completed(self, now: datetime | None = None) -> None:
        """Bump the campaign's completed counter as outreach records finish."""
        if self.status != CareCallbackCampaignStatus.ACTIVE:
            raise InvalidStateError(
                f"Cannot record completions on a {self.status.value} campaign"
            )
        self.completed_count += 1
        self.updated_at = now or utc_now()

    def progress_ratio(self) -> float:
        """Convenience: completed / target as a 0..1 ratio (0 when target is 0)."""
        if self.target_count == 0:
            return 0.0
        return min(self.completed_count / self.target_count, 1.0)
