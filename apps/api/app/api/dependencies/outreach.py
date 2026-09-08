"""Repository dependency factories for the outreach bounded context."""

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.domain.repositories.care_callback_repository import (
    CareCallbackCampaignRepository,
    OutreachRecordRepository,
)
from app.domain.repositories.survey_repository import (
    SurveyCampaignRepository,
    SurveyResponseRepository,
)
from app.domain.repositories.survey_source_repository import SurveySourceRepository


async def get_care_callback_campaign_repository(
    db: AsyncSession = Depends(get_db),
) -> "CareCallbackCampaignRepository":
    from app.infrastructure.repositories.care_callback_repository import (
        CareCallbackCampaignRepositoryImpl,
    )

    return CareCallbackCampaignRepositoryImpl(db)


async def get_outreach_record_repository(
    db: AsyncSession = Depends(get_db),
) -> "OutreachRecordRepository":
    from app.infrastructure.repositories.care_callback_repository import (
        OutreachRecordRepositoryImpl,
    )

    return OutreachRecordRepositoryImpl(db)


async def get_survey_campaign_repository(
    db: AsyncSession = Depends(get_db),
) -> "SurveyCampaignRepository":
    from app.infrastructure.repositories.survey_repository import (
        SurveyCampaignRepositoryImpl,
    )

    return SurveyCampaignRepositoryImpl(db)


async def get_survey_source_repository(
    db: AsyncSession = Depends(get_db),
) -> "SurveySourceRepository":
    from app.infrastructure.repositories.survey_source_repository import (
        SurveySourceRepositoryImpl,
    )

    return SurveySourceRepositoryImpl(db)


async def get_survey_response_repository(
    db: AsyncSession = Depends(get_db),
) -> "SurveyResponseRepository":
    from app.infrastructure.repositories.survey_repository import (
        SurveyResponseRepositoryImpl,
    )

    return SurveyResponseRepositoryImpl(db)


# =============================================================================
# =============================================================================
# EVENT BUS
# =============================================================================
