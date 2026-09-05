"""Repository dependency factories for the reporting bounded context."""

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.domain.repositories.report_repository import (
    ReportRunRepository,
    ReportTemplateRepository,
)
from app.domain.repositories.utilisation_event_repository import (
    UtilisationEventRepository,
)


async def get_report_template_repository(
    db: AsyncSession = Depends(get_db),
) -> "ReportTemplateRepository":
    from app.infrastructure.repositories.report_repository import (
        ReportTemplateRepositoryImpl,
    )

    return ReportTemplateRepositoryImpl(db)


async def get_report_run_repository(
    db: AsyncSession = Depends(get_db),
) -> "ReportRunRepository":
    from app.infrastructure.repositories.report_repository import (
        ReportRunRepositoryImpl,
    )

    return ReportRunRepositoryImpl(db)


async def get_report_query_runner(db: AsyncSession = Depends(get_db)):
    from app.infrastructure.services.report_query_runner import ReportQueryRunner

    return ReportQueryRunner(db)


async def get_utilisation_event_repository(
    db: AsyncSession = Depends(get_db),
) -> "UtilisationEventRepository":
    from app.infrastructure.repositories.utilisation_event_repository import (
        UtilisationEventRepositoryImpl,
    )

    return UtilisationEventRepositoryImpl(db)
