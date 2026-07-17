"""Outbox dispatcher (Phase 1 #C10).

Iterates undelivered outbox rows and routes each to its consumer. The audit
consumer is built-in; future consumers (notifications, reports) register via
:meth:`OutboxDispatcher.register_consumer`.

Concurrency model: a single worker process. Two workers running against the
same database are *safe* (each row is updated by id) but inefficient — pin
the worker to one replica until SELECT ... FOR UPDATE SKIP LOCKED is wired.
"""

from __future__ import annotations

import logging
from collections.abc import Awaitable, Callable
from datetime import timedelta

from app.domain.repositories.outbox_repository import (
    OutboxEventDTO,
    OutboxRepository,
)
from app.shared.utils.datetime import utc_now

logger = logging.getLogger(__name__)

Consumer = Callable[[OutboxEventDTO], Awaitable[None]]


def _backoff(attempts: int) -> timedelta:
    seconds = min(2 ** max(attempts, 0), 600)
    return timedelta(seconds=seconds)


class OutboxDispatcher:
    """Drives delivery from the outbox to registered consumers."""

    def __init__(self, repository: OutboxRepository):
        self._repository = repository
        self._consumers: list[Consumer] = []

    def register_consumer(self, consumer: Consumer) -> None:
        self._consumers.append(consumer)

    async def drain_once(self, *, batch_size: int = 100) -> int:
        """Process one batch of undelivered events; return the count delivered."""
        events = await self._repository.fetch_undelivered(limit=batch_size)
        delivered = 0
        for event in events:
            try:
                await self._dispatch(event)
            except Exception as exc:
                logger.exception("outbox: dispatch failed for %s", event.id)
                next_at = utc_now() + _backoff(event.delivery_attempts + 1)
                await self._repository.mark_failed(event.id, str(exc), next_at)
                continue
            await self._repository.mark_delivered(event.id)
            delivered += 1
        return delivered

    async def _dispatch(self, event: OutboxEventDTO) -> None:
        for consumer in self._consumers:
            await consumer(event)
