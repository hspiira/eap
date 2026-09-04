"""Repository dependency factories for the organization bounded context."""

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.domain.repositories.activity_repository import ActivityRepository
from app.domain.repositories.client_alias_repository import ClientAliasRepository
from app.domain.repositories.client_repository import ClientRepository
from app.domain.repositories.client_tag_repository import ClientTagRepository
from app.domain.repositories.industry_repository import IndustryRepository
from app.infrastructure.repositories.activity_repository import ActivityRepositoryImpl
from app.infrastructure.repositories.client_alias_repository import ClientAliasRepositoryImpl
from app.infrastructure.repositories.client_repository import ClientRepositoryImpl
from app.infrastructure.repositories.client_tag_repository import ClientTagRepositoryImpl
from app.infrastructure.repositories.industry_repository import IndustryRepositoryImpl


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


async def get_client_alias_repository(
    db: AsyncSession = Depends(get_db),
) -> ClientAliasRepository:
    """Dependency for tenant-scoped client alias persistence."""
    return ClientAliasRepositoryImpl(db)


async def get_industry_repository(
    db: AsyncSession = Depends(get_db),
) -> IndustryRepository:
    """
    Dependency for getting industry repository.

    Args:
        db: Database session (injected by FastAPI)

    Returns:
        IndustryRepository implementation
    """
    return IndustryRepositoryImpl(db)


async def get_client_tag_repository(
    db: AsyncSession = Depends(get_db),
) -> ClientTagRepository:
    """
    Dependency for getting client tag repository.

    Args:
        db: Database session (injected by FastAPI)

    Returns:
        ClientTagRepository implementation
    """
    return ClientTagRepositoryImpl(db)


async def get_activity_repository(
    db: AsyncSession = Depends(get_db),
) -> ActivityRepository:
    """
    Dependency for getting activity repository.

    Args:
        db: Database session (injected by FastAPI)

    Returns:
        ActivityRepository implementation
    """
    return ActivityRepositoryImpl(db)
