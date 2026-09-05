"""Repository dependency factories for the audit bounded context."""

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.domain.repositories.audit_repository import AuditRepository
from app.domain.repositories.outbox_repository import OutboxRepository
from app.infrastructure.repositories.audit_repository import AuditRepositoryImpl
from app.shared.handlers.audit_event_handler import AuditEventHandler


async def get_audit_repository(
    db: AsyncSession = Depends(get_db),
) -> AuditRepository:
    """
    Dependency for getting audit repository.

    Args:
        db: Database session (injected by FastAPI)

    Returns:
        AuditRepository implementation
    """
    return AuditRepositoryImpl(db)


async def get_outbox_repository(
    db: AsyncSession = Depends(get_db),
) -> "OutboxRepository":
    from app.infrastructure.repositories.outbox_repository import OutboxRepositoryImpl

    return OutboxRepositoryImpl(db)


async def get_audit_event_handler(
    outbox_repo: "OutboxRepository" = Depends(get_outbox_repository),
) -> AuditEventHandler:
    """Audit handler enqueues domain events on the transactional outbox."""
    return AuditEventHandler(outbox_repo)
