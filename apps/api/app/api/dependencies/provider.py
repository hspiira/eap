"""Repository dependency factories for the provider bounded context."""

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.domain.repositories.non_compete_clause_repository import (
    NonCompeteClauseRepository,
)
from app.domain.repositories.provider_repository import ProviderRepository
from app.domain.repositories.session_attribution_reader import SessionAttributionReader
from app.domain.repositories.session_name_reader import SessionNameReader


async def get_non_compete_clause_repository(
    db: AsyncSession = Depends(get_db),
) -> "NonCompeteClauseRepository":
    from app.infrastructure.repositories.non_compete_clause_repository import (
        NonCompeteClauseRepositoryImpl,
    )

    return NonCompeteClauseRepositoryImpl(db)


async def get_provider_repository(db: AsyncSession = Depends(get_db)) -> ProviderRepository:
    from app.infrastructure.repositories.provider_repository import ProviderRepositoryImpl

    return ProviderRepositoryImpl(db)


async def get_session_attribution_reader(
    db: AsyncSession = Depends(get_db),
) -> SessionAttributionReader:
    from app.infrastructure.repositories.session_attribution_reader import (
        SqlSessionAttributionReader,
    )

    return SqlSessionAttributionReader(db)


async def get_session_name_reader(
    db: AsyncSession = Depends(get_db),
) -> SessionNameReader:
    from app.infrastructure.repositories.session_name_reader import SqlSessionNameReader

    return SqlSessionNameReader(db)
