"""
API Dependencies

FastAPI dependency injection helpers.
"""

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.domain.repositories.client_repository import ClientRepository
from app.domain.repositories.tenant_repository import TenantRepository
from app.domain.repositories.user_repository import UserRepository
from app.infrastructure.repositories.client_repository import ClientRepositoryImpl
from app.infrastructure.repositories.tenant_repository import TenantRepositoryImpl
from app.infrastructure.repositories.user_repository import UserRepositoryImpl


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
