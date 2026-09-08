"""Service category taxonomy routes.

Replaces the ``ServiceCategory`` enum: a coarse grouping used by EAP programme
caps and authorization rules, now a table so a new category does not need a
code deploy and a migration.
"""

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import get_service_category_repository
from app.api.schemas.service_category_schemas import (
    ServiceCategoryCreate,
    ServiceCategoryResponse,
    ServiceCategoryUpdate,
)
from app.core.authorization import require_platform_admin
from app.core.database import get_db
from app.core.security import TokenData, get_current_user
from app.domain.repositories.service_category_repository import (
    ServiceCategoryRepository,
)
from app.shared.decorators import readonly, transactional

router = APIRouter(prefix="/service-categories", tags=["service-categories"])


@router.get("", response_model=list[ServiceCategoryResponse], summary="List service categories")
@readonly()
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
    _user: TokenData = Depends(require_platform_admin),
    repo: ServiceCategoryRepository = Depends(get_service_category_repository),
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
    return ServiceCategoryResponse.model_validate(created)


@router.patch("/{category_id}", response_model=ServiceCategoryResponse)
@transactional()
async def update_service_category(
    category_id: str,
    data: ServiceCategoryUpdate,
    _user: TokenData = Depends(require_platform_admin),
    repo: ServiceCategoryRepository = Depends(get_service_category_repository),
    db: AsyncSession = Depends(get_db),
):
    updated = await repo.update(
        category_id, name=data.name, description=data.description, sort_order=data.sort_order
    )
    if updated is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Service category not found")
    return ServiceCategoryResponse.model_validate(updated)


@router.post("/{category_id}/active", response_model=ServiceCategoryResponse)
@transactional()
async def set_service_category_active(
    category_id: str,
    is_active: bool = Query(..., description="Activate or retire the category"),
    _user: TokenData = Depends(require_platform_admin),
    repo: ServiceCategoryRepository = Depends(get_service_category_repository),
    db: AsyncSession = Depends(get_db),
):
    updated = await repo.set_active(category_id, is_active=is_active)
    if updated is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Service category not found")
    return ServiceCategoryResponse.model_validate(updated)
