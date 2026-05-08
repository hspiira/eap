"""Survey response entity (Phase 3 #D-Survey / SAD §5.2.7 / §6.4).

One ingested webhook delivery from an external survey provider. The
``external_response_id`` plus ``campaign_id`` form the idempotency key — re-deliveries
are detected and dropped at the repository layer (unique constraint).
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any

from app.domain.events import DomainEvent, SurveyResponseIngested
from app.domain.exceptions import DomainError
from app.domain.value_objects.core import (
    SurveyCampaignId,
    SurveyResponseId,
    TenantId,
)


@dataclass
class SurveyResponse:
    """One row in the campaign's response table."""

    id: SurveyResponseId
    tenant_id: TenantId
    campaign_id: SurveyCampaignId
    external_response_id: str
    submitted_at: datetime
    payload: dict[str, Any]
    received_at: datetime
    metrics: dict[str, Any] | None = None
    events: list[DomainEvent] = field(default_factory=list)

    def __post_init__(self) -> None:
        if not self.external_response_id:
            raise DomainError("SurveyResponse requires external_response_id")
        if self.submitted_at.tzinfo is None:
            raise DomainError("submitted_at must be timezone-aware")
        if self.received_at.tzinfo is None:
            raise DomainError("received_at must be timezone-aware")
        if not self.events:
            self.events.append(
                SurveyResponseIngested(
                    occurred_at=self.received_at,
                    response_id=self.id,
                    campaign_id=self.campaign_id,
                    external_response_id=self.external_response_id,
                )
            )
