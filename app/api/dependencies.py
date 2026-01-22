"""
API Dependencies

FastAPI dependency injection helpers.
"""

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.domain.repositories.tenant_repository import TenantRepository
from app.infrastructure.repositories.tenant_repository import TenantRepositoryImpl


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
