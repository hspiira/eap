"""Queued client import job runner.

Runs a persisted import job outside the request that created it. The job
row is the unit of progress reporting; the imported clients are one unit
of work that either commits whole or not at all.
"""

from __future__ import annotations

import logging
from contextlib import AbstractAsyncContextManager
from datetime import datetime
from typing import Any, Protocol

from app.application.services import client_import
from app.application.services.client_import import ImportRepositories
from app.core.security import TokenData
from app.domain.value_objects.core import TenantId
from app.shared.utils.client_csv import parse_client_csv
from app.shared.utils.datetime import utc_now

logger = logging.getLogger(__name__)

_PROGRESS_INTERVAL = 25


class ImportJobRecord(Protocol):
    """The persisted job row, as this service uses it.

    Structural so the application layer does not import the ORM model; the
    composition root passes the real one.
    """

    tenant_id: str
    requested_by: str
    file_content: bytes
    decisions: dict
    status: str
    total_rows: int
    processed_rows: int
    imported: int
    skipped: int
    failed: int
    issues: list
    error_message: str | None
    started_at: datetime | None
    completed_at: datetime | None


class ImportJobGateway(Protocol):
    """Infrastructure the runner needs, supplied by the composition root."""

    def session(self) -> AbstractAsyncContextManager[Any]:
        """A fresh unit of work."""

    async def load(self, session: Any, job_id: str) -> ImportJobRecord | None:
        """The job row within the given session, or None if it is gone."""

    def repositories(self, session: Any) -> ImportRepositories:
        """Repositories bound to the given session."""

    def audit_handler(self, session: Any) -> Any:
        """An audit handler writing to the outbox in the given session."""


async def _claim(gateway: ImportJobGateway, session: Any, job_id: str) -> ImportJobRecord | None:
    """Mark the job as processing in its own transaction so progress is visible."""
    job = await gateway.load(session, job_id)
    if job is None:
        logger.warning("client import: job %s no longer exists", job_id)
        return None
    job.status = "processing"
    job.started_at = utc_now()
    job.error_message = None
    await session.commit()
    return job


async def _record_failure(gateway: ImportJobGateway, job_id: str, error: str) -> None:
    """Record a failure in a session that never saw the failed transaction."""
    async with gateway.session() as session:
        job = await gateway.load(session, job_id)
        if job is None:
            return
        job.status = "failed"
        job.error_message = error[:1000]
        job.completed_at = utc_now()
        await session.commit()


async def _import_rows(gateway: ImportJobGateway, session: Any, job: ImportJobRecord) -> None:
    """Validate and create every row, recording the outcome on the job.

    Raises to abort the whole import.
    """
    rows, issues = parse_client_csv(job.file_content)
    tenant_id = TenantId(job.tenant_id)
    decisions = {int(key): value for key, value in (job.decisions or {}).items()}
    repos = gateway.repositories(session)

    result = await client_import.validate(rows, tenant_id, repos, decisions, issues)

    job.total_rows = len(rows)
    job.issues = issues

    if result.errors:
        job.imported = 0
        job.skipped = result.skipped
        job.failed = len(result.errors)
        job.processed_rows = len(rows)
        return

    current_user = TokenData(user_id=job.requested_by, tenant_id=job.tenant_id)
    audit_handler = gateway.audit_handler(session)

    async def update_progress(processed: int) -> None:
        # Progress is advisory. Flushing it inside the import transaction keeps
        # the row count honest without committing a partial import.
        if processed % _PROGRESS_INTERVAL == 0:
            job.processed_rows = processed
            await session.flush()

    created, failed = await client_import.create_clients(
        result.ready,
        tenant_id,
        repos,
        current_user,
        decisions,
        result.all_matches,
        issues,
        audit_handler,
        progress_callback=update_progress,
    )
    job.imported = len(created)
    job.skipped = result.skipped
    job.failed = failed
    job.processed_rows = len(rows)


async def run_import_job(job_id: str, gateway: ImportJobGateway) -> None:
    """Process a queued import after the request that queued it has committed.

    Claiming the job and recording its outcome are separate transactions from
    the import itself, so a failed import rolls back every client it created
    while still leaving the job row marked failed.
    """
    async with gateway.session() as session:
        job = await _claim(gateway, session, job_id)
        if job is None:
            return

    try:
        async with gateway.session() as session:
            job = await gateway.load(session, job_id)
            if job is None:
                return
            await _import_rows(gateway, session, job)
            job.status = "completed"
            job.completed_at = utc_now()
            await session.commit()
    except Exception as exc:
        logger.exception("client import: job %s failed", job_id)
        await _record_failure(gateway, job_id, str(exc))
