"""Outbox repository port (Phase 1 #C10)."""

from __future__ import annotations

from abc import ABC, abstractmethod
from datetime import datetime
from typing import Any


class OutboxRepository(ABC):
    """Port for the transactional outbox.

    `enqueue` runs in the caller's open transaction so the event row is
    committed atomically with the action that produced it. The worker
    (`scripts/outbox_worker.py`) calls `fetch_undelivered`, then either
    `mark_delivered` or `mark_failed` per record.
    """

    @abstractmethod
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
        """Insert a new outbox row and return its id."""

    @abstractmethod
    async def fetch_undelivered(self, *, limit: int = 100) -> list[OutboxEventDTO]: ...

    @abstractmethod
    async def mark_delivered(self, event_id: str) -> None: ...

    @abstractmethod
    async def mark_failed(
        self,
        event_id: str,
        error: str,
        next_attempt_at: datetime | None = None,
    ) -> None: ...

    @abstractmethod
    async def backlog(self) -> OutboxBacklog:
        """How far behind the worker is, for a liveness check."""


class OutboxBacklog:
    """Depth and staleness of the undelivered queue.

    Depth alone does not indicate a fault: a bulk import enqueues thousands of
    rows a healthy worker clears in seconds. Age does. An event still
    undelivered hours after it occurred means the worker is stopped, crashing
    or wedged, which is the state that went unnoticed for four days.
    """

    __slots__ = ("depth", "oldest_undelivered", "failed")

    def __init__(
        self,
        *,
        depth: int,
        oldest_undelivered: datetime | None,
        failed: int,
    ) -> None:
        self.depth = depth
        self.oldest_undelivered = oldest_undelivered
        self.failed = failed

    def age_seconds(self, *, now: datetime) -> float | None:
        """Seconds since the oldest undelivered event occurred, or None if empty."""
        if self.oldest_undelivered is None:
            return None
        return (now - self.oldest_undelivered).total_seconds()


class OutboxEventDTO:
    """Lightweight DTO returned by `fetch_undelivered`. Not a domain entity."""

    __slots__ = (
        "id",
        "tenant_id",
        "event_type",
        "payload",
        "occurred_at",
        "aggregate_type",
        "aggregate_id",
        "delivery_attempts",
    )

    def __init__(
        self,
        *,
        id: str,
        tenant_id: str,
        event_type: str,
        payload: dict[str, Any],
        occurred_at: datetime,
        aggregate_type: str | None,
        aggregate_id: str | None,
        delivery_attempts: int,
    ) -> None:
        self.id = id
        self.tenant_id = tenant_id
        self.event_type = event_type
        self.payload = payload
        self.occurred_at = occurred_at
        self.aggregate_type = aggregate_type
        self.aggregate_id = aggregate_id
        self.delivery_attempts = delivery_attempts
