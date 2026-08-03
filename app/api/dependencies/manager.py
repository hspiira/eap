"""Repository dependency factories for the manager bounded context."""

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.domain.repositories.manager_workspace_repository import (
    ManagerConsultRepository,
    TrainingEnrolmentRepository,
    WorkLifeProviderRepository,
    WorkLifeReferralRepository,
)
from app.domain.repositories.outcomes_repository import (
    FitnessForDutyRepository,
    OutcomeMeasureRepository,
    ReturnToWorkPlanRepository,
)


async def get_manager_consult_repository(
    db: AsyncSession = Depends(get_db),
) -> "ManagerConsultRepository":
    from app.infrastructure.repositories.manager_workspace_repository import (
        ManagerConsultRepositoryImpl,
    )

    return ManagerConsultRepositoryImpl(db)


async def get_work_life_provider_repository(
    db: AsyncSession = Depends(get_db),
) -> "WorkLifeProviderRepository":
    from app.infrastructure.repositories.manager_workspace_repository import (
        WorkLifeProviderRepositoryImpl,
    )

    return WorkLifeProviderRepositoryImpl(db)


async def get_work_life_referral_repository(
    db: AsyncSession = Depends(get_db),
) -> "WorkLifeReferralRepository":
    from app.infrastructure.repositories.manager_workspace_repository import (
        WorkLifeReferralRepositoryImpl,
    )

    return WorkLifeReferralRepositoryImpl(db)


async def get_training_enrolment_repository(
    db: AsyncSession = Depends(get_db),
) -> "TrainingEnrolmentRepository":
    from app.infrastructure.repositories.manager_workspace_repository import (
        TrainingEnrolmentRepositoryImpl,
    )

    return TrainingEnrolmentRepositoryImpl(db)


async def get_outcome_measure_repository(
    db: AsyncSession = Depends(get_db),
) -> "OutcomeMeasureRepository":
    from app.infrastructure.repositories.outcomes_repository import (
        OutcomeMeasureRepositoryImpl,
    )

    return OutcomeMeasureRepositoryImpl(db)


async def get_fitness_for_duty_repository(
    db: AsyncSession = Depends(get_db),
) -> "FitnessForDutyRepository":
    from app.infrastructure.repositories.outcomes_repository import (
        FitnessForDutyRepositoryImpl,
    )

    return FitnessForDutyRepositoryImpl(db)


async def get_return_to_work_plan_repository(
    db: AsyncSession = Depends(get_db),
) -> "ReturnToWorkPlanRepository":
    from app.infrastructure.repositories.outcomes_repository import (
        ReturnToWorkPlanRepositoryImpl,
    )

    return ReturnToWorkPlanRepositoryImpl(db)
