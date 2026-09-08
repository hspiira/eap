"""Utilisation event type taxonomy routes.

Replaces the ``UtilisationEventType`` enum: a new type is now a row an
operator adds through this API, not a code deploy.
"""

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import get_utilisation_event_type_repository
from app.api.schemas.utilisation_event_type_schemas import (
    UtilisationEventTypeCreate,
    UtilisationEventTypeResponse,
    UtilisationEventTypeUpdate,
)
from app.core.authorization import require_platform_admin
from app.core.database import get_db
from app.core.security import TokenData, get_current_user
from app.domain.repositories.utilisation_event_type_repository import (
    UtilisationEventTypeRepository,
)
from app.shared.decorators import readonly, transactional

router = APIRouter(prefix="/utilisation-event-types", tags=["utilisation-event-types"])


@router.get(
    "", response_model=list[UtilisationEventTypeResponse], summary="List utilisation event types"
)
@readonly()
async def list_utilisation_event_types(
    active_only: bool = Query(True, description="Return only active rows"),
    _user: TokenData = Depends(get_current_user),
    repo: UtilisationEventTypeRepository = Depends(get_utilisation_event_type_repository),
    db: AsyncSession = Depends(get_db),
):
    types = await repo.list_all(active_only=active_only)
    return [UtilisationEventTypeResponse.model_validate(t) for t in types]


@router.post("", response_model=UtilisationEventTypeResponse, status_code=status.HTTP_201_CREATED)
@transactional()
async def create_utilisation_event_type(
    data: UtilisationEventTypeCreate,
    _user: TokenData = Depends(require_platform_admin),
    repo: UtilisationEventTypeRepository = Depends(get_utilisation_event_type_repository),
    db: AsyncSession = Depends(get_db),
):
    if await repo.get_by_code(data.code):
        raise HTTPException(status.HTTP_409_CONFLICT, detail="Code already exists")
    created = await repo.create(
        code=data.code, name=data.name, description=data.description, sort_order=data.sort_order
    )
    return UtilisationEventTypeResponse.model_validate(created)


@router.patch("/{event_type_id}", response_model=UtilisationEventTypeResponse)
@transactional()
async def update_utilisation_event_type(
    event_type_id: str,
    data: UtilisationEventTypeUpdate,
    _user: TokenData = Depends(require_platform_admin),
    repo: UtilisationEventTypeRepository = Depends(get_utilisation_event_type_repository),
    db: AsyncSession = Depends(get_db),
):
    updated = await repo.update(
        event_type_id, name=data.name, description=data.description, sort_order=data.sort_order
    )
    if updated is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Utilisation event type not found")
    return UtilisationEventTypeResponse.model_validate(updated)


@router.post("/{event_type_id}/active", response_model=UtilisationEventTypeResponse)
@transactional()
async def set_utilisation_event_type_active(
    event_type_id: str,
    is_active: bool = Query(..., description="Activate or retire the row"),
    _user: TokenData = Depends(require_platform_admin),
    repo: UtilisationEventTypeRepository = Depends(get_utilisation_event_type_repository),
    db: AsyncSession = Depends(get_db),
):
    updated = await repo.set_active(event_type_id, is_active=is_active)
    if updated is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Utilisation event type not found")
    return UtilisationEventTypeResponse.model_validate(updated)
