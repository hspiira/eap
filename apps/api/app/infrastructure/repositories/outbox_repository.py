"""SQLAlchemy implementation of the outbox repository (Phase 1 #C10)."""

from __future__ import annotations

from datetime import datetime
from typing import Any

from sqlalchemy import func, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.repositories.outbox_repository import (
    OutboxBacklog,
    OutboxEventDTO,
    OutboxRepository,
)
from app.infrastructure.models.outbox_model import OutboxEventModel
from app.shared.utils.datetime import utc_now
from app.shared.utils.generators import generate_cuid


class OutboxRepositoryImpl(OutboxRepository):
    """Persists outbox rows in the caller's session.

    `enqueue` does not commit; the surrounding transactional decorator on
    the route owns the commit. That is what makes the outbox transactional
    with the action.
    """

    def __init__(self, session: AsyncSession):
        self._session = session

    async def enqueue(
        self,
        *,
        tenant_id: str,
        event_type: str,
        payload: dict[str, Any],
        occurred_at: datetime,
        aggregate_type: str | None = None,
        aggregate_id: str | None = None,
    ) -> str:
        row_id = generate_cuid()
        row = OutboxEventModel(
            id=row_id,
            tenant_id=tenant_id,
            event_type=event_type,
            payload=payload,
            aggregate_type=aggregate_type,
            aggregate_id=aggregate_id,
            occurred_at=occurred_at,
            delivery_attempts=0,
        )
        self._session.add(row)
        await self._session.flush()
        return row_id

    async def fetch_undelivered(self, *, limit: int = 100) -> list[OutboxEventDTO]:
        now = utc_now()
        stmt = (
            select(OutboxEventModel)
            .where(
                OutboxEventModel.delivered_at.is_(None),
                (OutboxEventModel.next_attempt_at.is_(None))
                | (OutboxEventModel.next_attempt_at <= now),
            )
            .order_by(OutboxEventModel.created_at)
            .limit(limit)
        )
        result = await self._session.execute(stmt)
        rows = result.scalars().all()
        return [
            OutboxEventDTO(
                id=row.id,
                tenant_id=row.tenant_id,
                event_type=row.event_type,
                payload=row.payload,
                occurred_at=row.occurred_at,
                aggregate_type=row.aggregate_type,
                aggregate_id=row.aggregate_id,
                delivery_attempts=row.delivery_attempts,
            )
            for row in rows
        ]

    async def mark_delivered(self, event_id: str) -> None:
        stmt = (
            update(OutboxEventModel)
            .where(OutboxEventModel.id == event_id)
            .values(
                delivered_at=utc_now(),
                last_error=None,
                next_attempt_at=None,
            )
        )
        await self._session.execute(stmt)

    async def mark_failed(
        self,
        event_id: str,
        error: str,
        next_attempt_at: datetime | None = None,
    ) -> None:
        stmt = (
            update(OutboxEventModel)
            .where(OutboxEventModel.id == event_id)
            .values(
                last_error=error,
                delivery_attempts=OutboxEventModel.delivery_attempts + 1,
                next_attempt_at=next_attempt_at,
            )
        )
        await self._session.execute(stmt)

    async def backlog(self) -> OutboxBacklog:
        undelivered = OutboxEventModel.delivered_at.is_(None)
        stmt = select(
            func.count().filter(undelivered),
            func.min(OutboxEventModel.occurred_at).filter(undelivered),
            func.count().filter(undelivered & OutboxEventModel.last_error.isnot(None)),
        )
        depth, oldest, failed = (await self._session.execute(stmt)).one()
        return OutboxBacklog(
            depth=depth or 0,
            oldest_undelivered=oldest,
            failed=failed or 0,
        )
