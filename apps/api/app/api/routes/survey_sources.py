"""Survey source taxonomy routes.

Replaces the ``SurveySource`` enum, whose docstring already called it
"extensible": a new source is now a row an operator adds through this API,
not a code deploy.
"""

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import get_survey_source_repository
from app.api.schemas.survey_source_schemas import (
    SurveySourceCreate,
    SurveySourceResponse,
    SurveySourceUpdate,
)
from app.core.authorization import require_platform_admin
from app.core.database import get_db
from app.core.reference_cache import cached_lookup, invalidate_reference_cache
from app.core.security import TokenData, get_current_user
from app.domain.repositories.survey_source_repository import SurveySourceRepository
from app.shared.decorators import readonly, transactional

router = APIRouter(prefix="/survey-sources", tags=["survey-sources"])

_RESOURCE = "survey_sources"


@router.get("", response_model=list[SurveySourceResponse], summary="List survey sources")
@readonly()
@cached_lookup(_RESOURCE)
async def list_survey_sources(
    active_only: bool = Query(True, description="Return only active rows"),
    _user: TokenData = Depends(get_current_user),
    repo: SurveySourceRepository = Depends(get_survey_source_repository),
    db: AsyncSession = Depends(get_db),
):
    sources = await repo.list_all(active_only=active_only)
    return [SurveySourceResponse.model_validate(s) for s in sources]


@router.post("", response_model=SurveySourceResponse, status_code=status.HTTP_201_CREATED)
@transactional()
async def create_survey_source(
    data: SurveySourceCreate,
    _user: TokenData = Depends(require_platform_admin),
    repo: SurveySourceRepository = Depends(get_survey_source_repository),
    db: AsyncSession = Depends(get_db),
):
    if await repo.get_by_code(data.code):
        raise HTTPException(status.HTTP_409_CONFLICT, detail="Code already exists")
    created = await repo.create(
        code=data.code, name=data.name, description=data.description, sort_order=data.sort_order
    )
    invalidate_reference_cache(_RESOURCE)
    return SurveySourceResponse.model_validate(created)


@router.patch("/{source_id}", response_model=SurveySourceResponse)
@transactional()
async def update_survey_source(
    source_id: str,
    data: SurveySourceUpdate,
    _user: TokenData = Depends(require_platform_admin),
    repo: SurveySourceRepository = Depends(get_survey_source_repository),
    db: AsyncSession = Depends(get_db),
):
    updated = await repo.update(
        source_id, name=data.name, description=data.description, sort_order=data.sort_order
    )
    if updated is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Survey source not found")
    invalidate_reference_cache(_RESOURCE)
    return SurveySourceResponse.model_validate(updated)


@router.post("/{source_id}/active", response_model=SurveySourceResponse)
@transactional()
async def set_survey_source_active(
    source_id: str,
    is_active: bool = Query(..., description="Activate or retire the row"),
    _user: TokenData = Depends(require_platform_admin),
    repo: SurveySourceRepository = Depends(get_survey_source_repository),
    db: AsyncSession = Depends(get_db),
):
    updated = await repo.set_active(source_id, is_active=is_active)
    if updated is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Survey source not found")
    invalidate_reference_cache(_RESOURCE)
    return SurveySourceResponse.model_validate(updated)
