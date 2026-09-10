"""Next-of-kin relationship taxonomy routes.

Replaces the ``NextOfKinRelationship`` enum, whose explicit ``OTHER`` member
was already evidence the fixed list was insufficient: a new value is now a
row an operator adds through this API, not a code deploy.
"""

from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import get_next_of_kin_relationship_repository
from app.api.dependencies.audit import get_audit_event_handler
from app.api.schemas.next_of_kin_relationship_schemas import (
    NextOfKinRelationshipCreate,
    NextOfKinRelationshipResponse,
    NextOfKinRelationshipUpdate,
)
from app.core.authorization import require_platform_admin
from app.core.database import get_db
from app.core.reference_cache import cached_lookup, invalidate_reference_cache
from app.core.security import TokenData, get_current_user
from app.domain.enums import AuditActionType
from app.domain.repositories.next_of_kin_relationship_repository import (
    NextOfKinRelationshipRepository,
)
from app.shared.decorators import readonly, transactional
from app.shared.utils.route_audit_helper import audit_reference_change

router = APIRouter(prefix="/next-of-kin-relationships", tags=["next-of-kin-relationships"])

_RESOURCE = "next_of_kin_relationships"


@router.get(
    "", response_model=list[NextOfKinRelationshipResponse], summary="List NOK relationships"
)
@readonly()
@cached_lookup(_RESOURCE)
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
    request: Request,
    _user: TokenData = Depends(require_platform_admin),
    repo: NextOfKinRelationshipRepository = Depends(get_next_of_kin_relationship_repository),
    audit_handler=Depends(get_audit_event_handler),
    db: AsyncSession = Depends(get_db),
):
    if await repo.get_by_code(data.code):
        raise HTTPException(status.HTTP_409_CONFLICT, detail="Code already exists")
    created = await repo.create(
        code=data.code, name=data.name, description=data.description, sort_order=data.sort_order
    )
    await audit_reference_change(
        audit_handler,
        _user,
        request,
        action=AuditActionType.CREATE,
        resource_type="NextOfKinRelationship",
        resource_id=created.id,
        after=created,
    )
    invalidate_reference_cache(_RESOURCE)
    return NextOfKinRelationshipResponse.model_validate(created)


@router.patch("/{relationship_id}", response_model=NextOfKinRelationshipResponse)
@transactional()
async def update_next_of_kin_relationship(
    relationship_id: str,
    data: NextOfKinRelationshipUpdate,
    request: Request,
    _user: TokenData = Depends(require_platform_admin),
    repo: NextOfKinRelationshipRepository = Depends(get_next_of_kin_relationship_repository),
    audit_handler=Depends(get_audit_event_handler),
    db: AsyncSession = Depends(get_db),
):
    before = await repo.get_by_id(relationship_id)
    updated = await repo.update(
        relationship_id,
        name=data.name,
        description=data.description,
        sort_order=data.sort_order,
    )
    if updated is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Relationship not found")
    await audit_reference_change(
        audit_handler,
        _user,
        request,
        action=AuditActionType.UPDATE,
        resource_type="NextOfKinRelationship",
        resource_id=updated.id,
        before=before,
        after=updated,
    )
    invalidate_reference_cache(_RESOURCE)
    return NextOfKinRelationshipResponse.model_validate(updated)


@router.post("/{relationship_id}/active", response_model=NextOfKinRelationshipResponse)
@transactional()
async def set_next_of_kin_relationship_active(
    relationship_id: str,
    request: Request,
    is_active: bool = Query(..., description="Activate or retire the row"),
    _user: TokenData = Depends(require_platform_admin),
    repo: NextOfKinRelationshipRepository = Depends(get_next_of_kin_relationship_repository),
    audit_handler=Depends(get_audit_event_handler),
    db: AsyncSession = Depends(get_db),
):
    before = await repo.get_by_id(relationship_id)
    updated = await repo.set_active(relationship_id, is_active=is_active)
    if updated is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Relationship not found")
    await audit_reference_change(
        audit_handler,
        _user,
        request,
        action=AuditActionType.UPDATE,
        resource_type="NextOfKinRelationship",
        resource_id=updated.id,
        before=before,
        after=updated,
    )
    invalidate_reference_cache(_RESOURCE)
    return NextOfKinRelationshipResponse.model_validate(updated)
