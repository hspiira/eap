"""Repository dependency factories for the tenancy bounded context."""

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.domain.repositories.tenant_repository import TenantRepository
from app.infrastructure.repositories.password_set_token_repository import (
    PasswordSetTokenRepository,
)
from app.infrastructure.repositories.refresh_token_repository import (
    RefreshTokenRepository,
)
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


async def get_password_set_token_repository(
    db: AsyncSession = Depends(get_db),
) -> PasswordSetTokenRepository:
    """Dependency for password set token store (tenant creation set-password flow)."""
    return PasswordSetTokenRepository(db)


async def get_refresh_token_repository(
    db: AsyncSession = Depends(get_db),
) -> RefreshTokenRepository:
    """Dependency for refresh token repository (revocation/rotation)."""
    return RefreshTokenRepository(db)
