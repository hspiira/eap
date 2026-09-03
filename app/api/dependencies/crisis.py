"""Repository dependency factories for the crisis bounded context."""

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.domain.repositories.critical_incident_repository import (
    CriticalIncidentRepository,
)


async def get_critical_incident_repository(
    db: AsyncSession = Depends(get_db),
) -> "CriticalIncidentRepository":
    from app.infrastructure.repositories.critical_incident_repository import (
        CriticalIncidentRepositoryImpl,
    )

    return CriticalIncidentRepositoryImpl(db)
