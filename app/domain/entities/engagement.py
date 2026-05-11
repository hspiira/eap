"""Engagement aggregate (Phase 4 #D-Engagement / SAD §5.2.8).

Cluster B consultancy projects. An ``Engagement`` is owned by one client and
composes (a) a list of ``Deliverable``s with their own per-item status and
(b) ``HoursLogEntry`` rows tracking effort logged by Minet users. The whole
aggregate moves through Draft → Active → Delivered → Invoiced → Closed; the
deliverable list is mutable while the engagement is Draft / Active and frozen
once Delivered.
"""

from dataclasses import dataclass, field
from datetime import date, datetime

from app.domain.enums import DeliverableStatus, EngagementStatus
from app.domain.events import (
    DomainEvent,
    EngagementActivated,
    EngagementClosed,
    EngagementCreated,
    EngagementDelivered,
    EngagementInvoiced,
    HoursLogged,
)
from app.domain.exceptions import DomainError, InvalidStateError
from app.domain.value_objects.core import (
    ClientId,
    DeliverableId,
    EngagementId,
    HoursLogEntryId,
    TenantId,
    UserId,
)
from app.shared.utils.datetime import utc_now


@dataclass
class Deliverable:
    """One contractual artefact the engagement promises to produce.

    Tracked as an entity inside the Engagement aggregate (mutable status, but
    same lifetime as the parent — never queried independently).
    """

    id: DeliverableId
    title: str
    description: str | None
    due_date: date | None
    status: DeliverableStatus = DeliverableStatus.PENDING
    delivered_at: datetime | None = None

    def __post_init__(self) -> None:
        if not self.title:
            raise DomainError("Deliverable requires a title")

    def start(self) -> None:
        if self.status != DeliverableStatus.PENDING:
            raise InvalidStateError(
                f"Cannot start a {self.status.value} deliverable"
            )
        self.status = DeliverableStatus.IN_PROGRESS

    def deliver(self, *, when: datetime | None = None) -> None:
        if self.status not in {
            DeliverableStatus.PENDING,
            DeliverableStatus.IN_PROGRESS,
        }:
            raise InvalidStateError(
                f"Cannot deliver a {self.status.value} deliverable"
            )
        self.status = DeliverableStatus.DELIVERED
        self.delivered_at = when or utc_now()

    def accept(self) -> None:
        if self.status != DeliverableStatus.DELIVERED:
            raise InvalidStateError(
                f"Cannot accept a {self.status.value} deliverable"
            )
        self.status = DeliverableStatus.ACCEPTED


@dataclass(frozen=True)
class HoursLogEntry:
    """One time-log line: a Minet user, a date, an hours float, an optional note."""

    id: HoursLogEntryId
    user_id: UserId
    logged_on: date
    hours: float
    note: str | None = None

    def __post_init__(self) -> None:
        if self.hours <= 0:
            raise DomainError("HoursLogEntry.hours must be positive")
        if self.hours > 24:
            raise DomainError("HoursLogEntry.hours cannot exceed 24 per entry")


@dataclass
class Engagement:
    """A Cluster B consultancy project owned by one client."""

    id: EngagementId
    tenant_id: TenantId
    client_id: ClientId
    name: str
    status: EngagementStatus
    created_by: UserId
    created_at: datetime
    updated_at: datetime
    description: str | None = None
    period_start: date | None = None
    period_end: date | None = None
    deliverables: list[Deliverable] = field(default_factory=list[Deliverable])
    hours_log: list[HoursLogEntry] = field(default_factory=list[HoursLogEntry])
    activated_at: datetime | None = None
    delivered_at: datetime | None = None
    invoiced_at: datetime | None = None
    closed_at: datetime | None = None
    events: list[DomainEvent] = field(default_factory=list[DomainEvent])

    def __post_init__(self) -> None:
        if not self.name:
            raise DomainError("Engagement requires a name")
        if (
            self.period_start
            and self.period_end
            and self.period_end < self.period_start
        ):
            raise DomainError("period_end must be on or after period_start")
        if self.created_at == self.updated_at and not self.events:
            self.events.append(
                EngagementCreated(
                    occurred_at=self.created_at,
                    engagement_id=self.id,
                    tenant_id=self.tenant_id,
                    client_id=self.client_id,
                )
            )

    def _is_open(self) -> bool:
        return self.status in {EngagementStatus.DRAFT, EngagementStatus.ACTIVE}

    def add_deliverable(
        self,
        *,
        deliverable_id: DeliverableId,
        title: str,
        description: str | None = None,
        due_date: date | None = None,
    ) -> Deliverable:
        if not self._is_open():
            raise InvalidStateError(
                f"Cannot add deliverables to a {self.status.value} engagement"
            )
        d = Deliverable(
            id=deliverable_id,
            title=title,
            description=description,
            due_date=due_date,
        )
        self.deliverables.append(d)
        self.updated_at = utc_now()
        return d

    def remove_deliverable(self, deliverable_id: DeliverableId) -> None:
        if not self._is_open():
            raise InvalidStateError(
                f"Cannot remove deliverables from a {self.status.value} engagement"
            )
        before = len(self.deliverables)
        self.deliverables = [
            d for d in self.deliverables if d.id != deliverable_id
        ]
        if len(self.deliverables) == before:
            raise DomainError(f"Deliverable not found: {deliverable_id.value}")
        self.updated_at = utc_now()

    def _find_deliverable(self, deliverable_id: DeliverableId) -> Deliverable:
        for d in self.deliverables:
            if d.id == deliverable_id:
                return d
        raise DomainError(f"Deliverable not found: {deliverable_id.value}")

    def update_deliverable_status(
        self,
        *,
        deliverable_id: DeliverableId,
        status: DeliverableStatus,
    ) -> Deliverable:
        if self.status not in {EngagementStatus.ACTIVE, EngagementStatus.DRAFT}:
            raise InvalidStateError(
                f"Cannot update deliverables on a {self.status.value} engagement"
            )
        d = self._find_deliverable(deliverable_id)
        if status == DeliverableStatus.IN_PROGRESS:
            d.start()
        elif status == DeliverableStatus.DELIVERED:
            d.deliver()
        elif status == DeliverableStatus.ACCEPTED:
            d.accept()
        else:
            raise DomainError(
                f"Use add_deliverable to set initial status; got {status.value}"
            )
        self.updated_at = utc_now()
        return d

    def log_hours(
        self,
        *,
        entry_id: HoursLogEntryId,
        user_id: UserId,
        logged_on: date,
        hours: float,
        note: str | None = None,
    ) -> HoursLogEntry:
        if self.status == EngagementStatus.CLOSED:
            raise InvalidStateError("Cannot log hours on a closed engagement")
        entry = HoursLogEntry(
            id=entry_id,
            user_id=user_id,
            logged_on=logged_on,
            hours=hours,
            note=note,
        )
        self.hours_log.append(entry)
        self.updated_at = utc_now()
        self.events.append(
            HoursLogged(
                occurred_at=self.updated_at,
                engagement_id=self.id,
                user_id=user_id,
                hours=hours,
            )
        )
        return entry

    def total_hours(self) -> float:
        return sum(e.hours for e in self.hours_log)

    def hours_by_user(self) -> dict[str, float]:
        out: dict[str, float] = {}
        for e in self.hours_log:
            out[e.user_id.value] = out.get(e.user_id.value, 0.0) + e.hours
        return out

    def activate(self, now: datetime | None = None) -> None:
        if self.status != EngagementStatus.DRAFT:
            raise InvalidStateError(
                f"Cannot activate an engagement in status {self.status.value}"
            )
        if not self.deliverables:
            raise DomainError("Cannot activate an engagement with no deliverables")
        now = now or utc_now()
        self.status = EngagementStatus.ACTIVE
        self.activated_at = now
        self.updated_at = now
        self.events.append(
            EngagementActivated(occurred_at=now, engagement_id=self.id)
        )

    def deliver(self, now: datetime | None = None) -> None:
        if self.status != EngagementStatus.ACTIVE:
            raise InvalidStateError(
                f"Cannot mark delivered from status {self.status.value}"
            )
        outstanding = [
            d
            for d in self.deliverables
            if d.status not in {DeliverableStatus.DELIVERED, DeliverableStatus.ACCEPTED}
        ]
        if outstanding:
            raise DomainError(
                f"Cannot mark engagement delivered: {len(outstanding)} deliverable(s) "
                "are still outstanding"
            )
        now = now or utc_now()
        self.status = EngagementStatus.DELIVERED
        self.delivered_at = now
        self.updated_at = now
        self.events.append(
            EngagementDelivered(occurred_at=now, engagement_id=self.id)
        )

    def invoice(self, now: datetime | None = None) -> None:
        if self.status != EngagementStatus.DELIVERED:
            raise InvalidStateError(
                f"Cannot invoice an engagement in status {self.status.value}"
            )
        now = now or utc_now()
        self.status = EngagementStatus.INVOICED
        self.invoiced_at = now
        self.updated_at = now
        self.events.append(
            EngagementInvoiced(occurred_at=now, engagement_id=self.id)
        )

    def close(self, now: datetime | None = None) -> None:
        if self.status != EngagementStatus.INVOICED:
            raise InvalidStateError(
                f"Cannot close an engagement in status {self.status.value}"
            )
        now = now or utc_now()
        self.status = EngagementStatus.CLOSED
        self.closed_at = now
        self.updated_at = now
        self.events.append(
            EngagementClosed(occurred_at=now, engagement_id=self.id)
        )
