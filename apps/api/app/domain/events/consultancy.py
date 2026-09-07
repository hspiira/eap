"""Domain events for the consultancy bounded context."""

from dataclasses import dataclass

from app.domain.events.base import DomainEvent
from app.domain.value_objects.core import (
    ClientId,
    DeliverableId,
    EngagementId,
    TenantId,
    UserId,
)


@dataclass(frozen=True)
class EngagementCreated(DomainEvent):
    engagement_id: "EngagementId"
    tenant_id: TenantId
    client_id: ClientId


@dataclass(frozen=True)
class EngagementActivated(DomainEvent):
    engagement_id: "EngagementId"


@dataclass(frozen=True)
class EngagementDelivered(DomainEvent):
    engagement_id: "EngagementId"


@dataclass(frozen=True)
class EngagementInvoiced(DomainEvent):
    engagement_id: "EngagementId"


@dataclass(frozen=True)
class EngagementClosed(DomainEvent):
    engagement_id: "EngagementId"


@dataclass(frozen=True)
class HoursLogged(DomainEvent):
    engagement_id: "EngagementId"
    user_id: UserId
    hours: float


@dataclass(frozen=True)
class DeliverableAdded(DomainEvent):
    engagement_id: "EngagementId"
    deliverable_id: DeliverableId
    title: str


@dataclass(frozen=True)
class DeliverableStatusChanged(DomainEvent):
    engagement_id: "EngagementId"
    deliverable_id: DeliverableId
    from_status: str
    to_status: str
