"""Queued client import job runner.

Runs a persisted import job outside the request that created it. The job
row is the unit of progress reporting; the imported clients are one unit
of work that either commits whole or not at all.
"""

from __future__ import annotations

import logging

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.application.services import client_import
from app.application.services.client_import import ImportRepositories
from app.core.security import TokenData
from app.domain.value_objects.core import TenantId
from app.infrastructure.models.client_import_job_model import ClientImportJobModel
from app.infrastructure.repositories.client_alias_repository import ClientAliasRepositoryImpl
from app.infrastructure.repositories.client_repository import ClientRepositoryImpl
from app.infrastructure.repositories.industry_repository import IndustryRepositoryImpl
from app.infrastructure.repositories.outbox_repository import OutboxRepositoryImpl
from app.infrastructure.repositories.tenant_repository import TenantRepositoryImpl
from app.shared.handlers.audit_event_handler import AuditEventHandler
from app.shared.utils.client_csv import parse_client_csv
from app.shared.utils.datetime import utc_now

logger = logging.getLogger(__name__)

_PROGRESS_INTERVAL = 25


def _repositories(session: AsyncSession) -> ImportRepositories:
    return ImportRepositories(
        client=ClientRepositoryImpl(session),
        alias=ClientAliasRepositoryImpl(session),
        industry=IndustryRepositoryImpl(session),
        tenant=TenantRepositoryImpl(session),
    )


async def _claim(session: AsyncSession, job_id: str) -> ClientImportJobModel | None:
    """Mark the job as processing in its own transaction so progress is visible."""
    job = await session.get(ClientImportJobModel, job_id)
    if job is None:
        logger.warning("client import: job %s no longer exists", job_id)
        return None
    job.status = "processing"
    job.started_at = utc_now()
    job.error_message = None
    await session.commit()
    return job


async def _record_failure(
    session_factory: async_sessionmaker[AsyncSession], job_id: str, error: str
) -> None:
    """Record a failure in a session that never saw the failed transaction."""
    async with session_factory() as session:
        job = await session.get(ClientImportJobModel, job_id)
        if job is None:
            return
        job.status = "failed"
        job.error_message = error[:1000]
        job.completed_at = utc_now()
        await session.commit()


async def _import_rows(session: AsyncSession, job: ClientImportJobModel) -> dict[str, int | list]:
    """Validate and create every row. Raises to abort the whole import."""
    rows, issues = parse_client_csv(job.file_content)
    tenant_id = TenantId(job.tenant_id)
    decisions = {int(key): value for key, value in (job.decisions or {}).items()}
    repos = _repositories(session)

    result = await client_import.validate(rows, tenant_id, repos, decisions, issues)

    job.total_rows = len(rows)
    job.issues = issues

    if result.errors:
        return {
            "imported": 0,
            "skipped": result.skipped,
            "failed": len(result.errors),
            "processed_rows": len(rows),
            "issues": issues,
        }

    current_user = TokenData(user_id=job.requested_by, tenant_id=job.tenant_id)
    audit_handler = AuditEventHandler(OutboxRepositoryImpl(session))

    async def update_progress(processed: int) -> None:
        # Progress is advisory. Flushing it inside the import transaction keeps
        # the row count honest without committing a partial import.
        if processed % _PROGRESS_INTERVAL == 0:
            job.processed_rows = processed
            await session.flush()

    created, decision_skipped, decision_failed = await client_import.create_clients(
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
    return {
        "imported": len(created),
        "skipped": result.skipped + decision_skipped,
        "failed": decision_failed,
        "processed_rows": len(rows),
        "issues": issues,
    }


async def run_import_job(job_id: str, session_factory: async_sessionmaker[AsyncSession]) -> None:
    """Process a queued import after the request that queued it has committed.

    Claiming the job and recording its outcome are separate transactions from
    the import itself, so a failed import rolls back every client it created
    while still leaving the job row marked failed.
    """
    async with session_factory() as session:
        job = await _claim(session, job_id)
        if job is None:
            return

    try:
        async with session_factory() as session:
            job = await session.get(ClientImportJobModel, job_id)
            if job is None:
                return
            outcome = await _import_rows(session, job)
            job.imported = outcome["imported"]
            job.skipped = outcome["skipped"]
            job.failed = outcome["failed"]
            job.processed_rows = outcome["processed_rows"]
            job.issues = outcome["issues"]
            job.status = "completed"
            job.completed_at = utc_now()
            await session.commit()
    except Exception as exc:
        logger.exception("client import: job %s failed", job_id)
        await _record_failure(session_factory, job_id, str(exc))
