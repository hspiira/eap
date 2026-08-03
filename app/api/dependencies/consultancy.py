"""Repository dependency factories for the consultancy bounded context."""

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.domain.repositories.engagement_repository import EngagementRepository


async def get_engagement_repository(
    db: AsyncSession = Depends(get_db),
) -> "EngagementRepository":
    from app.infrastructure.repositories.engagement_repository import (
        EngagementRepositoryImpl,
    )

    return EngagementRepositoryImpl(db)
