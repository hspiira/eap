"""Composition root for the provider network repositories.

A new module rather than an addition to `provider.py`, so agent 2's wiring does
not edit a file agent 1 owns. Follows the same pattern: infrastructure is
imported here and injected into routes.
"""

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies.delivery import get_service_session_repository
from app.api.dependencies.provider import get_provider_repository
from app.application.use_cases.historical_session_import import (
    RecordHistoricalSessionUseCase,
)
from app.core.database import get_db
from app.domain.repositories.affiliation_attribution_guard import (
    AffiliationAttributionGuard,
)
from app.domain.repositories.provider_network_repository import (
    ProviderAffiliationRepository,
    ProviderAliasRepository,
    ProviderOrganisationRepository,
    ProviderSpecialtyRepository,
    SessionImportRepository,
)
from app.domain.repositories.provider_repository import ProviderRepository
from app.domain.repositories.service_session_repository import ServiceSessionRepository


async def get_provider_organisation_repository(
    db: AsyncSession = Depends(get_db),
) -> ProviderOrganisationRepository:
    from app.infrastructure.repositories.provider_network_repository import (
        ProviderOrganisationRepositoryImpl,
    )

    return ProviderOrganisationRepositoryImpl(db)


async def get_provider_affiliation_repository(
    db: AsyncSession = Depends(get_db),
) -> ProviderAffiliationRepository:
    from app.infrastructure.repositories.provider_network_repository import (
        ProviderAffiliationRepositoryImpl,
    )

    return ProviderAffiliationRepositoryImpl(db)


async def get_provider_specialty_repository(
    db: AsyncSession = Depends(get_db),
) -> ProviderSpecialtyRepository:
    from app.infrastructure.repositories.provider_network_repository import (
        ProviderSpecialtyRepositoryImpl,
    )

    return ProviderSpecialtyRepositoryImpl(db)


async def get_provider_alias_repository(
    db: AsyncSession = Depends(get_db),
) -> ProviderAliasRepository:
    from app.infrastructure.repositories.provider_network_repository import (
        ProviderAliasRepositoryImpl,
    )

    return ProviderAliasRepositoryImpl(db)


async def get_session_import_repository(
    db: AsyncSession = Depends(get_db),
) -> SessionImportRepository:
    from app.infrastructure.repositories.provider_network_repository import (
        SessionImportRepositoryImpl,
    )

    return SessionImportRepositoryImpl(db)


async def get_affiliation_attribution_guard(
    db: AsyncSession = Depends(get_db),
) -> AffiliationAttributionGuard:
    """The real attribution check, reading session attribution.

    This replaces the fail-closed placeholder that refused every narrowing
    while the check was unwired. Widening is still answered without a query.
    """
    from app.infrastructure.repositories.affiliation_attribution_guard import (
        SqlAffiliationAttributionGuard,
    )

    return SqlAffiliationAttributionGuard(db)


async def get_historical_session_writer(
    session_repo: ServiceSessionRepository = Depends(get_service_session_repository),
    provider_repo: ProviderRepository = Depends(get_provider_repository),
):
    """The adapter onto the historical write path.

    Application-layer, not infrastructure: it is pure translation between a
    staged row and the record the write path takes, with no database or
    transport concern. That also keeps it off the routes-to-infrastructure
    allowlist.

    The use case is injected even though the adapter refuses before it would
    reach it, so that when member and service resolution lands the wiring is
    already correct rather than a None waiting to be found.
    """
    from app.application.services.historical_session_writer import (
        HistoricalSessionWriterAdapter,
    )

    return HistoricalSessionWriterAdapter(
        record_use_case=RecordHistoricalSessionUseCase(session_repo, provider_repo)
    )
