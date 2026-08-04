"""Repository dependency factories for the crisis bounded context."""

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.domain.repositories.crisis_contact_repository import (
    CrisisContactRepository,
)
from app.domain.repositories.critical_incident_repository import (
    CriticalIncidentRepository,
)
from app.domain.repositories.risk_safety_repository import (
    CaringContactRepository,
    MandatoryReportRepository,
    RiskAssessmentRepository,
    SafetyPlanRepository,
)


async def get_critical_incident_repository(
    db: AsyncSession = Depends(get_db),
) -> "CriticalIncidentRepository":
    from app.infrastructure.repositories.critical_incident_repository import (
        CriticalIncidentRepositoryImpl,
    )

    return CriticalIncidentRepositoryImpl(db)


async def get_crisis_contact_repository(
    db: AsyncSession = Depends(get_db),
) -> "CrisisContactRepository":
    from app.infrastructure.repositories.crisis_contact_repository import (
        CrisisContactRepositoryImpl,
    )

    return CrisisContactRepositoryImpl(db)


async def get_risk_assessment_repository(
    db: AsyncSession = Depends(get_db),
) -> "RiskAssessmentRepository":
    from app.infrastructure.repositories.risk_safety_repository import (
        RiskAssessmentRepositoryImpl,
    )

    return RiskAssessmentRepositoryImpl(db)


async def get_safety_plan_repository(
    db: AsyncSession = Depends(get_db),
) -> "SafetyPlanRepository":
    from app.infrastructure.repositories.risk_safety_repository import (
        SafetyPlanRepositoryImpl,
    )

    return SafetyPlanRepositoryImpl(db)


async def get_mandatory_report_repository(
    db: AsyncSession = Depends(get_db),
) -> "MandatoryReportRepository":
    from app.infrastructure.repositories.risk_safety_repository import (
        MandatoryReportRepositoryImpl,
    )

    return MandatoryReportRepositoryImpl(db)


async def get_caring_contact_repository(
    db: AsyncSession = Depends(get_db),
) -> "CaringContactRepository":
    from app.infrastructure.repositories.risk_safety_repository import (
        CaringContactRepositoryImpl,
    )

    return CaringContactRepositoryImpl(db)
