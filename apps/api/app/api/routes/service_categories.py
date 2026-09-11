"""Service category taxonomy routes.

Replaces the ``ServiceCategory`` enum: a coarse grouping used by EAP programme
caps and authorization rules, now a table so a new category does not need a
code deploy and a migration.
"""

from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import get_service_category_repository
from app.api.dependencies.audit import get_audit_event_handler
from app.api.schemas.service_category_schemas import (
    ServiceCategoryCreate,
    ServiceCategoryResponse,
    ServiceCategoryUpdate,
)
from app.core.authorization import require_platform_admin
from app.core.database import get_db
from app.core.reference_cache import cached_lookup, invalidate_reference_cache
from app.core.security import TokenData, get_current_user
from app.domain.enums import AuditActionType
from app.domain.repositories.service_category_repository import (
    ServiceCategoryRepository,
)
from app.shared.decorators import readonly, transactional
from app.shared.utils.route_audit_helper import audit_reference_change

router = APIRouter(prefix="/service-categories", tags=["service-categories"])

_RESOURCE = "service_categories"


@router.get("", response_model=list[ServiceCategoryResponse], summary="List service categories")
@readonly()
@cached_lookup(_RESOURCE)
async def list_service_categories(
    active_only: bool = Query(True, description="Return only active categories"),
    _user: TokenData = Depends(get_current_user),
    repo: ServiceCategoryRepository = Depends(get_service_category_repository),
    db: AsyncSession = Depends(get_db),
):
    categories = await repo.list_all(active_only=active_only)
    return [ServiceCategoryResponse.model_validate(c) for c in categories]


@router.post("", response_model=ServiceCategoryResponse, status_code=status.HTTP_201_CREATED)
@transactional()
async def create_service_category(
    data: ServiceCategoryCreate,
    request: Request,
    _user: TokenData = Depends(require_platform_admin),
    repo: ServiceCategoryRepository = Depends(get_service_category_repository),
    audit_handler=Depends(get_audit_event_handler),
    db: AsyncSession = Depends(get_db),
):
    if await repo.get_by_code(data.code):
        raise HTTPException(status.HTTP_409_CONFLICT, detail="Category code already exists")
    created = await repo.create(
        code=data.code,
        name=data.name,
        description=data.description,
        sort_order=data.sort_order,
    )
    await audit_reference_change(
        audit_handler,
        _user,
        request,
        action=AuditActionType.CREATE,
        resource_type="ServiceCategory",
        resource_id=created.id,
        after=created,
    )
    await invalidate_reference_cache(_RESOURCE)
    return ServiceCategoryResponse.model_validate(created)


@router.patch("/{category_id}", response_model=ServiceCategoryResponse)
@transactional()
async def update_service_category(
    category_id: str,
    data: ServiceCategoryUpdate,
    request: Request,
    _user: TokenData = Depends(require_platform_admin),
    repo: ServiceCategoryRepository = Depends(get_service_category_repository),
    audit_handler=Depends(get_audit_event_handler),
    db: AsyncSession = Depends(get_db),
):
    before = await repo.get_by_id(category_id)
    updated = await repo.update(
        category_id, name=data.name, description=data.description, sort_order=data.sort_order
    )
    if updated is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Service category not found")
    await audit_reference_change(
        audit_handler,
        _user,
        request,
        action=AuditActionType.UPDATE,
        resource_type="ServiceCategory",
        resource_id=updated.id,
        before=before,
        after=updated,
    )
    await invalidate_reference_cache(_RESOURCE)
    return ServiceCategoryResponse.model_validate(updated)


@router.post("/{category_id}/active", response_model=ServiceCategoryResponse)
@transactional()
async def set_service_category_active(
    category_id: str,
    request: Request,
    is_active: bool = Query(..., description="Activate or retire the category"),
    _user: TokenData = Depends(require_platform_admin),
    repo: ServiceCategoryRepository = Depends(get_service_category_repository),
    audit_handler=Depends(get_audit_event_handler),
    db: AsyncSession = Depends(get_db),
):
    before = await repo.get_by_id(category_id)
    updated = await repo.set_active(category_id, is_active=is_active)
    if updated is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Service category not found")
    await audit_reference_change(
        audit_handler,
        _user,
        request,
        action=AuditActionType.UPDATE,
        resource_type="ServiceCategory",
        resource_id=updated.id,
        before=before,
        after=updated,
    )
    await invalidate_reference_cache(_RESOURCE)
    return ServiceCategoryResponse.model_validate(updated)
