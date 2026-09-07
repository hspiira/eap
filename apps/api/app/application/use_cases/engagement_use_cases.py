"""Engagement use cases (Phase 4 #D-Engagement).

Bespoke create + structural-mutation paths (deliverables, hours). FSM transitions
(``activate`` / ``deliver`` / ``invoice`` / ``close``) flow through the existing
``TransitionUseCase`` + ``EngagementTransition`` enum.

Each structural mutation returns the mutated aggregate alongside the child it
produced. The aggregate carries the domain events the route hands to the audit
trail; returning only the child left the events unreachable and unaudited.
"""

from __future__ import annotations

from datetime import date

from app.application.use_cases.base import BaseUseCase
from app.domain.entities.engagement import Deliverable, Engagement, HoursLogEntry
from app.domain.enums import DeliverableStatus, EngagementStatus
from app.domain.exceptions import NotFoundError
from app.domain.repositories.engagement_repository import EngagementRepository
from app.domain.value_objects.core import (
    ClientId,
    DeliverableId,
    EngagementId,
    HoursLogEntryId,
    TenantId,
    UserId,
)
from app.shared.utils.datetime import utc_now
from app.shared.utils.generators import generate_cuid


class CreateEngagementUseCase(BaseUseCase[Engagement, EngagementId]):
    def __init__(self, repository: EngagementRepository):
        super().__init__(repository)

    async def execute(
        self,
        *,
        engagement_id: EngagementId,
        tenant_id: TenantId,
        client_id: ClientId,
        name: str,
        created_by: UserId,
        description: str | None = None,
        period_start: date | None = None,
        period_end: date | None = None,
    ) -> Engagement:
        now = utc_now()
        engagement = Engagement(
            id=engagement_id,
            tenant_id=tenant_id,
            client_id=client_id,
            name=name,
            description=description,
            status=EngagementStatus.DRAFT,
            period_start=period_start,
            period_end=period_end,
            created_by=created_by,
            created_at=now,
            updated_at=now,
        )
        return await self._save_and_publish_events(engagement)


def _load_or_404(engagement: Engagement | None, engagement_id: EngagementId) -> Engagement:
    if engagement is None:
        raise NotFoundError(
            f"Engagement not found: {engagement_id.value}",
            resource_type="Engagement",
            resource_id=engagement_id.value,
        )
    return engagement


class AddDeliverableUseCase:
    def __init__(self, repository: EngagementRepository):
        self._repo = repository

    async def execute(
        self,
        *,
        engagement_id: EngagementId,
        title: str,
        description: str | None = None,
        due_date: date | None = None,
    ) -> tuple[Engagement, Deliverable]:
        engagement = _load_or_404(await self._repo.get_by_id(engagement_id), engagement_id)
        deliverable = engagement.add_deliverable(
            deliverable_id=DeliverableId(generate_cuid()),
            title=title,
            description=description,
            due_date=due_date,
        )
        await self._repo.save(engagement)
        return engagement, deliverable


class UpdateDeliverableStatusUseCase:
    def __init__(self, repository: EngagementRepository):
        self._repo = repository

    async def execute(
        self,
        *,
        engagement_id: EngagementId,
        deliverable_id: DeliverableId,
        status: DeliverableStatus,
    ) -> tuple[Engagement, Deliverable]:
        engagement = _load_or_404(await self._repo.get_by_id(engagement_id), engagement_id)
        d = engagement.update_deliverable_status(deliverable_id=deliverable_id, status=status)
        await self._repo.save(engagement)
        return engagement, d


class LogHoursUseCase:
    def __init__(self, repository: EngagementRepository):
        self._repo = repository

    async def execute(
        self,
        *,
        engagement_id: EngagementId,
        user_id: UserId,
        logged_on: date,
        hours: float,
        note: str | None = None,
    ) -> tuple[Engagement, HoursLogEntry]:
        engagement = _load_or_404(await self._repo.get_by_id(engagement_id), engagement_id)
        entry = engagement.log_hours(
            entry_id=HoursLogEntryId(generate_cuid()),
            user_id=user_id,
            logged_on=logged_on,
            hours=hours,
            note=note,
        )
        await self._repo.save(engagement)
        return engagement, entry


class GetEngagementSummaryUseCase:
    """Read-side: engagement + total hours + per-user breakdown + deliverable mix."""

    def __init__(self, repository: EngagementRepository):
        self._repo = repository

    async def execute(self, engagement_id: EngagementId) -> dict:
        engagement = _load_or_404(await self._repo.get_by_id(engagement_id), engagement_id)
        deliverable_mix: dict[str, int] = {}
        for d in engagement.deliverables:
            deliverable_mix[d.status.value] = deliverable_mix.get(d.status.value, 0) + 1
        return {
            "engagement_id": engagement.id.value,
            "client_id": engagement.client_id.value,
            "name": engagement.name,
            "status": engagement.status.value,
            "deliverable_count": len(engagement.deliverables),
            "deliverable_mix": deliverable_mix,
            "total_hours": engagement.total_hours(),
            "hours_by_user": engagement.hours_by_user(),
            "period_start": engagement.period_start.isoformat()
            if engagement.period_start
            else None,
            "period_end": engagement.period_end.isoformat() if engagement.period_end else None,
            "generated_at": utc_now().isoformat(),
        }
