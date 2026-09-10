"""Outbox dispatcher tests (Phase 1 #C10)."""

from datetime import UTC, datetime, timedelta
from typing import Any

import pytest

from app.application.services.outbox_dispatcher import OutboxDispatcher
from app.domain.repositories.outbox_repository import (
    OutboxBacklog,
    OutboxEventDTO,
    OutboxRepository,
)


class _FakeRepo(OutboxRepository):
    def __init__(self, events: list[OutboxEventDTO]):
        self.events = list(events)
        self.delivered: list[str] = []
        self.failed: list[tuple[str, str, datetime | None]] = []

    async def enqueue(self, **kwargs: Any) -> str:
        raise NotImplementedError

    async def fetch_undelivered(self, *, limit: int = 100) -> list[OutboxEventDTO]:
        out = self.events[:limit]
        self.events = self.events[limit:]
        return out

    async def mark_delivered(self, event_id: str) -> None:
        self.delivered.append(event_id)

    async def mark_failed(
        self,
        event_id: str,
        error: str,
        next_attempt_at: datetime | None = None,
    ) -> None:
        self.failed.append((event_id, error, next_attempt_at))

    async def backlog(self) -> OutboxBacklog:
        return OutboxBacklog(depth=len(self.events), oldest_undelivered=None, failed=0)


def _event(id_: str, attempts: int = 0) -> OutboxEventDTO:
    return OutboxEventDTO(
        id=id_,
        tenant_id="t-1",
        event_type="UserActivated",
        payload={"action_type": "UPDATE"},
        occurred_at=datetime.now(UTC),
        aggregate_type="User",
        aggregate_id="u-1",
        delivery_attempts=attempts,
    )


class TestDrain:
    @pytest.mark.asyncio
    async def test_delivers_each_event_to_every_consumer(self):
        repo = _FakeRepo([_event("a"), _event("b")])
        seen: list[tuple[str, str]] = []

        async def consumer_one(e: OutboxEventDTO) -> None:
            seen.append(("one", e.id))

        async def consumer_two(e: OutboxEventDTO) -> None:
            seen.append(("two", e.id))

        d = OutboxDispatcher(repo)
        d.register_consumer(consumer_one)
        d.register_consumer(consumer_two)

        delivered = await d.drain_once()

        assert delivered == 2
        assert repo.delivered == ["a", "b"]
        assert ("one", "a") in seen and ("two", "a") in seen
        assert ("one", "b") in seen and ("two", "b") in seen

    @pytest.mark.asyncio
    async def test_failed_consumer_marks_and_continues(self):
        repo = _FakeRepo([_event("a"), _event("b")])

        async def flaky(e: OutboxEventDTO) -> None:
            if e.id == "a":
                raise RuntimeError("kaboom")

        d = OutboxDispatcher(repo)
        d.register_consumer(flaky)

        delivered = await d.drain_once()

        assert delivered == 1
        assert repo.delivered == ["b"]
        assert len(repo.failed) == 1
        failed_id, msg, next_at = repo.failed[0]
        assert failed_id == "a"
        assert "kaboom" in msg
        assert next_at is not None

    @pytest.mark.asyncio
    async def test_backoff_grows_with_attempts(self):
        repo = _FakeRepo([_event("a", attempts=3)])

        async def consumer(_: OutboxEventDTO) -> None:
            raise RuntimeError("still failing")

        d = OutboxDispatcher(repo)
        d.register_consumer(consumer)

        before = datetime.now(UTC)
        await d.drain_once()
        _, _, next_at = repo.failed[0]
        assert next_at is not None
        delta = next_at - before
        # Attempts becomes 4 inside _backoff(attempts + 1) → 2**4 = 16s.
        assert delta >= timedelta(seconds=10)

    @pytest.mark.asyncio
    async def test_empty_batch_returns_zero(self):
        repo = _FakeRepo([])
        d = OutboxDispatcher(repo)
        assert await d.drain_once() == 0
