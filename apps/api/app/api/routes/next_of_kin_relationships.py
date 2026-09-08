"""Next-of-kin relationship taxonomy routes.

Replaces the ``NextOfKinRelationship`` enum, whose explicit ``OTHER`` member
was already evidence the fixed list was insufficient: a new value is now a
row an operator adds through this API, not a code deploy.
"""

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import get_next_of_kin_relationship_repository
from app.api.schemas.next_of_kin_relationship_schemas import (
    NextOfKinRelationshipCreate,
    NextOfKinRelationshipResponse,
    NextOfKinRelationshipUpdate,
)
from app.core.authorization import require_platform_admin
from app.core.database import get_db
from app.core.security import TokenData, get_current_user
from app.domain.repositories.next_of_kin_relationship_repository import (
    NextOfKinRelationshipRepository,
)
from app.shared.decorators import readonly, transactional

router = APIRouter(prefix="/next-of-kin-relationships", tags=["next-of-kin-relationships"])


@router.get(
    "", response_model=list[NextOfKinRelationshipResponse], summary="List NOK relationships"
)
@readonly()
async def list_next_of_kin_relationships(
    active_only: bool = Query(True, description="Return only active rows"),
    _user: TokenData = Depends(get_current_user),
    repo: NextOfKinRelationshipRepository = Depends(get_next_of_kin_relationship_repository),
    db: AsyncSession = Depends(get_db),
):
    relationships = await repo.list_all(active_only=active_only)
    return [NextOfKinRelationshipResponse.model_validate(r) for r in relationships]


@router.post("", response_model=NextOfKinRelationshipResponse, status_code=status.HTTP_201_CREATED)
@transactional()
async def create_next_of_kin_relationship(
    data: NextOfKinRelationshipCreate,
    _user: TokenData = Depends(require_platform_admin),
    repo: NextOfKinRelationshipRepository = Depends(get_next_of_kin_relationship_repository),
    db: AsyncSession = Depends(get_db),
):
    if await repo.get_by_code(data.code):
        raise HTTPException(status.HTTP_409_CONFLICT, detail="Code already exists")
    created = await repo.create(
        code=data.code, name=data.name, description=data.description, sort_order=data.sort_order
    )
    return NextOfKinRelationshipResponse.model_validate(created)


@router.patch("/{relationship_id}", response_model=NextOfKinRelationshipResponse)
@transactional()
async def update_next_of_kin_relationship(
    relationship_id: str,
    data: NextOfKinRelationshipUpdate,
    _user: TokenData = Depends(require_platform_admin),
    repo: NextOfKinRelationshipRepository = Depends(get_next_of_kin_relationship_repository),
    db: AsyncSession = Depends(get_db),
):
    updated = await repo.update(
        relationship_id,
        name=data.name,
        description=data.description,
        sort_order=data.sort_order,
    )
    if updated is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Relationship not found")
    return NextOfKinRelationshipResponse.model_validate(updated)


@router.post("/{relationship_id}/active", response_model=NextOfKinRelationshipResponse)
@transactional()
async def set_next_of_kin_relationship_active(
    relationship_id: str,
    is_active: bool = Query(..., description="Activate or retire the row"),
    _user: TokenData = Depends(require_platform_admin),
    repo: NextOfKinRelationshipRepository = Depends(get_next_of_kin_relationship_repository),
    db: AsyncSession = Depends(get_db),
):
    updated = await repo.set_active(relationship_id, is_active=is_active)
    if updated is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Relationship not found")
    return NextOfKinRelationshipResponse.model_validate(updated)
