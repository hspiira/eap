"""
API Dependencies

FastAPI dependency injection helpers.
"""

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.domain.repositories.audit_repository import AuditRepository
from app.domain.repositories.client_repository import ClientRepository
from app.domain.repositories.contract_repository import ContractRepository
from app.domain.repositories.document_repository import DocumentRepository
from app.domain.repositories.person_repository import PersonRepository
from app.domain.repositories.service_repository import ServiceRepository
from app.domain.repositories.service_session_repository import (
    ServiceSessionRepository,
)
from app.domain.repositories.tenant_repository import TenantRepository
from app.domain.repositories.user_repository import UserRepository
from app.infrastructure.repositories.audit_repository import AuditRepositoryImpl
from app.infrastructure.repositories.client_repository import ClientRepositoryImpl
from app.infrastructure.repositories.contract_repository import ContractRepositoryImpl
from app.infrastructure.repositories.document_repository import DocumentRepositoryImpl
from app.infrastructure.repositories.person_repository import PersonRepositoryImpl
from app.infrastructure.repositories.service_repository import ServiceRepositoryImpl
from app.infrastructure.repositories.service_session_repository import (
    ServiceSessionRepositoryImpl,
)
from app.infrastructure.repositories.tenant_repository import TenantRepositoryImpl
from app.infrastructure.repositories.user_repository import UserRepositoryImpl
from app.shared.handlers.audit_event_handler import AuditEventHandler


async def get_tenant_repository(
    db: AsyncSession = Depends(get_db),
) -> TenantRepository:
    """
    Dependency for getting tenant repository.

    Args:
        db: Database session (injected by FastAPI)

    Returns:
        TenantRepository implementation
    """
    return TenantRepositoryImpl(db)


async def get_user_repository(
    db: AsyncSession = Depends(get_db),
) -> UserRepository:
    """
    Dependency for getting user repository.

    Args:
        db: Database session (injected by FastAPI)

    Returns:
        UserRepository implementation
    """
    return UserRepositoryImpl(db)


async def get_client_repository(
    db: AsyncSession = Depends(get_db),
) -> ClientRepository:
    """
    Dependency for getting client repository.

    Args:
        db: Database session (injected by FastAPI)

    Returns:
        ClientRepository implementation
    """
    return ClientRepositoryImpl(db)


async def get_person_repository(
    db: AsyncSession = Depends(get_db),
    user_repo: UserRepository = Depends(get_user_repository),
) -> PersonRepository:
    """
    Dependency for getting person repository.

    Args:
        db: Database session (injected by FastAPI)
        user_repo: User repository (injected dependency)

    Returns:
        PersonRepository implementation
    """
    return PersonRepositoryImpl(db, user_repo)


async def get_contract_repository(
    db: AsyncSession = Depends(get_db),
) -> ContractRepository:
    """
    Dependency for getting contract repository.

    Args:
        db: Database session (injected by FastAPI)

    Returns:
        ContractRepository implementation
    """
    return ContractRepositoryImpl(db)


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


async def get_service_repository(
    db: AsyncSession = Depends(get_db),
) -> ServiceRepository:
    """
    Dependency for getting service repository.

    Args:
        db: Database session (injected by FastAPI)

    Returns:
        ServiceRepository implementation
    """
    return ServiceRepositoryImpl(db)


async def get_service_session_repository(
    db: AsyncSession = Depends(get_db),
) -> ServiceSessionRepository:
    """
    Dependency for getting service session repository.

    Args:
        db: Database session (injected by FastAPI)

    Returns:
        ServiceSessionRepository implementation
    """
    return ServiceSessionRepositoryImpl(db)


async def get_document_repository(
    db: AsyncSession = Depends(get_db),
) -> DocumentRepository:
    """
    Dependency for getting document repository.

    Args:
        db: Database session (injected by FastAPI)

    Returns:
        DocumentRepository implementation
    """
    return DocumentRepositoryImpl(db)


async def get_audit_event_handler(
    audit_repo: AuditRepository = Depends(get_audit_repository),
) -> AuditEventHandler:
    """
    Dependency for getting audit event handler.

    Args:
        audit_repo: Audit repository (injected dependency)

    Returns:
        AuditEventHandler instance
    """
    return AuditEventHandler(audit_repo)
