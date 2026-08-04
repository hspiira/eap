"""Outbox worker (Phase 1 #C10).

Long-running process that drains the ``outbox_events`` table and dispatches
to registered consumers. Run as a separate container/service in production:

    uv run python scripts/outbox_worker.py

Each iteration picks up a batch of undelivered rows, processes them, and
sleeps briefly. Failed rows are retried with exponential backoff per the
``next_attempt_at`` column.
"""

from __future__ import annotations

import asyncio
import logging
import signal

from app.application.services.outbox_consumers import make_audit_consumer
from app.application.services.outbox_dispatcher import OutboxDispatcher
from app.core.database import AsyncSessionLocal
from app.infrastructure.repositories.audit_repository import AuditRepositoryImpl
from app.infrastructure.repositories.outbox_repository import OutboxRepositoryImpl

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s - %(message)s",
)
logger = logging.getLogger("outbox_worker")

_IDLE_SLEEP_SECONDS = 2.0
_BATCH_SIZE = 100


async def _run_once() -> int:
    async with AsyncSessionLocal() as session:
        outbox_repo = OutboxRepositoryImpl(session)
        audit_repo = AuditRepositoryImpl(session)
        dispatcher = OutboxDispatcher(outbox_repo)
        dispatcher.register_consumer(make_audit_consumer(audit_repo))
        delivered = await dispatcher.drain_once(batch_size=_BATCH_SIZE)
        await session.commit()
        return delivered


async def main() -> None:
    stopping = asyncio.Event()

    def _stop(*_: object) -> None:
        logger.info("outbox worker received stop signal")
        stopping.set()

    loop = asyncio.get_running_loop()
    for sig in (signal.SIGINT, signal.SIGTERM):
        loop.add_signal_handler(sig, _stop)

    logger.info("outbox worker started")
    while not stopping.is_set():
        try:
            delivered = await _run_once()
        except Exception:
            logger.exception("outbox worker iteration failed")
            await asyncio.sleep(_IDLE_SLEEP_SECONDS)
            continue
        if delivered == 0:
            try:
                await asyncio.wait_for(stopping.wait(), timeout=_IDLE_SLEEP_SECONDS)
            except TimeoutError:
                pass

    logger.info("outbox worker stopped")


if __name__ == "__main__":
    asyncio.run(main())
