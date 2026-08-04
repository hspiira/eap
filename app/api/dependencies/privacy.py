"""Repository dependency factories for the privacy bounded context."""

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.domain.repositories.benchmark_consent_repository import (
    BenchmarkConsentRepository,
)
from app.domain.repositories.consent_repository import (
    ConsentRepository,
    DataSharingRegisterRepository,
    DPOContactRepository,
)
from app.domain.repositories.dsar_repository import DSARRequestRepository


async def get_dsar_request_repository(
    db: AsyncSession = Depends(get_db),
) -> "DSARRequestRepository":
    from app.infrastructure.repositories.dsar_repository import (
        DSARRequestRepositoryImpl,
    )

    return DSARRequestRepositoryImpl(db)


async def get_dsar_collector(db: AsyncSession = Depends(get_db)):
    from app.infrastructure.services.dsar_service import SqlDSARDataCollector

    return SqlDSARDataCollector(db)


async def get_consent_repository(
    db: AsyncSession = Depends(get_db),
) -> "ConsentRepository":
    from app.infrastructure.repositories.consent_repository import (
        ConsentRepositoryImpl,
    )

    return ConsentRepositoryImpl(db)


async def get_data_sharing_register_repository(
    db: AsyncSession = Depends(get_db),
) -> "DataSharingRegisterRepository":
    from app.infrastructure.repositories.consent_repository import (
        DataSharingRegisterRepositoryImpl,
    )

    return DataSharingRegisterRepositoryImpl(db)


async def get_dpo_contact_repository(
    db: AsyncSession = Depends(get_db),
) -> "DPOContactRepository":
    from app.infrastructure.repositories.consent_repository import (
        DPOContactRepositoryImpl,
    )

    return DPOContactRepositoryImpl(db)


async def get_benchmark_consent_repository(
    db: AsyncSession = Depends(get_db),
) -> "BenchmarkConsentRepository":
    from app.infrastructure.repositories.benchmark_consent_repository import (
        BenchmarkConsentRepositoryImpl,
    )

    return BenchmarkConsentRepositoryImpl(db)


async def get_benchmark_collector(db: AsyncSession = Depends(get_db)):
    from app.infrastructure.services.benchmark_collector import (
        SqlBenchmarkCollector,
    )

    return SqlBenchmarkCollector(db)


async def get_dsar_tombstoner(db: AsyncSession = Depends(get_db)):
    from app.infrastructure.services.dsar_service import SqlDSARTombstoner

    return SqlDSARTombstoner(db)
