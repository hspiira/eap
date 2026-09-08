"""Client tier taxonomy routes.

Replaces the ``ClientTier`` enum: a new tier is now a row an operator adds
through this API, not a code deploy.
"""

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import get_client_tier_repository
from app.api.schemas.client_tier_schemas import (
    ClientTierCreate,
    ClientTierResponse,
    ClientTierUpdate,
)
from app.core.authorization import require_platform_admin
from app.core.database import get_db
from app.core.security import TokenData, get_current_user
from app.domain.repositories.client_tier_repository import ClientTierRepository
from app.shared.decorators import readonly, transactional

router = APIRouter(prefix="/client-tiers", tags=["client-tiers"])


@router.get("", response_model=list[ClientTierResponse], summary="List client tiers")
@readonly()
async def list_client_tiers(
    active_only: bool = Query(True, description="Return only active rows"),
    _user: TokenData = Depends(get_current_user),
    repo: ClientTierRepository = Depends(get_client_tier_repository),
    db: AsyncSession = Depends(get_db),
):
    tiers = await repo.list_all(active_only=active_only)
    return [ClientTierResponse.model_validate(t) for t in tiers]


@router.post("", response_model=ClientTierResponse, status_code=status.HTTP_201_CREATED)
@transactional()
async def create_client_tier(
    data: ClientTierCreate,
    _user: TokenData = Depends(require_platform_admin),
    repo: ClientTierRepository = Depends(get_client_tier_repository),
    db: AsyncSession = Depends(get_db),
):
    if await repo.get_by_code(data.code):
        raise HTTPException(status.HTTP_409_CONFLICT, detail="Code already exists")
    created = await repo.create(
        code=data.code, name=data.name, description=data.description, sort_order=data.sort_order
    )
    return ClientTierResponse.model_validate(created)


@router.patch("/{tier_id}", response_model=ClientTierResponse)
@transactional()
async def update_client_tier(
    tier_id: str,
    data: ClientTierUpdate,
    _user: TokenData = Depends(require_platform_admin),
    repo: ClientTierRepository = Depends(get_client_tier_repository),
    db: AsyncSession = Depends(get_db),
):
    updated = await repo.update(
        tier_id, name=data.name, description=data.description, sort_order=data.sort_order
    )
    if updated is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Client tier not found")
    return ClientTierResponse.model_validate(updated)


@router.post("/{tier_id}/active", response_model=ClientTierResponse)
@transactional()
async def set_client_tier_active(
    tier_id: str,
    is_active: bool = Query(..., description="Activate or retire the row"),
    _user: TokenData = Depends(require_platform_admin),
    repo: ClientTierRepository = Depends(get_client_tier_repository),
    db: AsyncSession = Depends(get_db),
):
    updated = await repo.set_active(tier_id, is_active=is_active)
    if updated is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Client tier not found")
    return ClientTierResponse.model_validate(updated)
