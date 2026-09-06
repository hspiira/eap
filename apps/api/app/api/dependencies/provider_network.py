"""Composition root for the provider network repositories.

A new module rather than an addition to `provider.py`, so agent 2's wiring does
not edit a file agent 1 owns. Follows the same pattern: infrastructure is
imported here and injected into routes.
"""

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.domain.repositories.provider_network_repository import (
    ProviderAffiliationRepository,
    ProviderAliasRepository,
    ProviderOrganisationRepository,
    ProviderSpecialtyRepository,
    SessionImportRepository,
)


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
