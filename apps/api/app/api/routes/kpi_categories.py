"""KPI category taxonomy routes.

Replaces the ``KPICategory`` enum: a new category is a row an operator adds
through this API, not a code deploy.
"""

from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import get_kpi_category_repository
from app.api.dependencies.audit import get_audit_event_handler
from app.api.schemas.kpi_category_schemas import (
    KPICategoryCreate,
    KPICategoryResponse,
    KPICategoryUpdate,
)
from app.core.authorization import require_platform_admin
from app.core.database import get_db
from app.core.reference_cache import cached_lookup, invalidate_reference_cache
from app.core.security import TokenData, get_current_user
from app.domain.enums import AuditActionType
from app.domain.repositories.kpi_category_repository import KPICategoryRepository
from app.shared.decorators import readonly, transactional
from app.shared.utils.route_audit_helper import audit_reference_change

router = APIRouter(prefix="/kpi-categories", tags=["kpi-categories"])

_RESOURCE = "kpi_categories"


@router.get("", response_model=list[KPICategoryResponse], summary="List KPI categories")
@readonly()
@cached_lookup(_RESOURCE)
async def list_kpi_categories(
    active_only: bool = Query(True, description="Return only active categories"),
    _user: TokenData = Depends(get_current_user),
    repo: KPICategoryRepository = Depends(get_kpi_category_repository),
    db: AsyncSession = Depends(get_db),
):
    categories = await repo.list_all(active_only=active_only)
    return [KPICategoryResponse.model_validate(c) for c in categories]


@router.post("", response_model=KPICategoryResponse, status_code=status.HTTP_201_CREATED)
@transactional()
async def create_kpi_category(
    data: KPICategoryCreate,
    request: Request,
    _user: TokenData = Depends(require_platform_admin),
    repo: KPICategoryRepository = Depends(get_kpi_category_repository),
    audit_handler=Depends(get_audit_event_handler),
    db: AsyncSession = Depends(get_db),
):
    if await repo.get_by_code(data.code):
        raise HTTPException(status.HTTP_409_CONFLICT, detail="Category code already exists")
    created = await repo.create(
        code=data.code, name=data.name, description=data.description, sort_order=data.sort_order
    )
    await audit_reference_change(
        audit_handler,
        _user,
        request,
        action=AuditActionType.CREATE,
        resource_type="KpiCategory",
        resource_id=created.id,
        after=created,
    )
    await invalidate_reference_cache(_RESOURCE)
    return KPICategoryResponse.model_validate(created)


@router.patch("/{category_id}", response_model=KPICategoryResponse)
@transactional()
async def update_kpi_category(
    category_id: str,
    data: KPICategoryUpdate,
    request: Request,
    _user: TokenData = Depends(require_platform_admin),
    repo: KPICategoryRepository = Depends(get_kpi_category_repository),
    audit_handler=Depends(get_audit_event_handler),
    db: AsyncSession = Depends(get_db),
):
    before = await repo.get_by_id(category_id)
    updated = await repo.update(
        category_id, name=data.name, description=data.description, sort_order=data.sort_order
    )
    if updated is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="KPI category not found")
    await audit_reference_change(
        audit_handler,
        _user,
        request,
        action=AuditActionType.UPDATE,
        resource_type="KpiCategory",
        resource_id=updated.id,
        before=before,
        after=updated,
    )
    await invalidate_reference_cache(_RESOURCE)
    return KPICategoryResponse.model_validate(updated)


@router.post("/{category_id}/active", response_model=KPICategoryResponse)
@transactional()
async def set_kpi_category_active(
    category_id: str,
    request: Request,
    is_active: bool = Query(..., description="Activate or retire the category"),
    _user: TokenData = Depends(require_platform_admin),
    repo: KPICategoryRepository = Depends(get_kpi_category_repository),
    audit_handler=Depends(get_audit_event_handler),
    db: AsyncSession = Depends(get_db),
):
    before = await repo.get_by_id(category_id)
    updated = await repo.set_active(category_id, is_active=is_active)
    if updated is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="KPI category not found")
    await audit_reference_change(
        audit_handler,
        _user,
        request,
        action=AuditActionType.UPDATE,
        resource_type="KpiCategory",
        resource_id=updated.id,
        before=before,
        after=updated,
    )
    await invalidate_reference_cache(_RESOURCE)
    return KPICategoryResponse.model_validate(updated)
