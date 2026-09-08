"""KPI measurement unit taxonomy routes.

Replaces the ``KPIMeasurementUnit`` enum: a new unit is now a row an operator
adds through this API, not a code deploy.
"""

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import get_kpi_measurement_unit_repository
from app.api.schemas.kpi_measurement_unit_schemas import (
    KPIMeasurementUnitCreate,
    KPIMeasurementUnitResponse,
    KPIMeasurementUnitUpdate,
)
from app.core.authorization import require_platform_admin
from app.core.database import get_db
from app.core.security import TokenData, get_current_user
from app.domain.repositories.kpi_measurement_unit_repository import (
    KPIMeasurementUnitRepository,
)
from app.shared.decorators import readonly, transactional

router = APIRouter(prefix="/kpi-measurement-units", tags=["kpi-measurement-units"])


@router.get(
    "", response_model=list[KPIMeasurementUnitResponse], summary="List KPI measurement units"
)
@readonly()
async def list_kpi_measurement_units(
    active_only: bool = Query(True, description="Return only active rows"),
    _user: TokenData = Depends(get_current_user),
    repo: KPIMeasurementUnitRepository = Depends(get_kpi_measurement_unit_repository),
    db: AsyncSession = Depends(get_db),
):
    units = await repo.list_all(active_only=active_only)
    return [KPIMeasurementUnitResponse.model_validate(u) for u in units]


@router.post("", response_model=KPIMeasurementUnitResponse, status_code=status.HTTP_201_CREATED)
@transactional()
async def create_kpi_measurement_unit(
    data: KPIMeasurementUnitCreate,
    _user: TokenData = Depends(require_platform_admin),
    repo: KPIMeasurementUnitRepository = Depends(get_kpi_measurement_unit_repository),
    db: AsyncSession = Depends(get_db),
):
    if await repo.get_by_code(data.code):
        raise HTTPException(status.HTTP_409_CONFLICT, detail="Code already exists")
    created = await repo.create(
        code=data.code, name=data.name, description=data.description, sort_order=data.sort_order
    )
    return KPIMeasurementUnitResponse.model_validate(created)


@router.patch("/{unit_id}", response_model=KPIMeasurementUnitResponse)
@transactional()
async def update_kpi_measurement_unit(
    unit_id: str,
    data: KPIMeasurementUnitUpdate,
    _user: TokenData = Depends(require_platform_admin),
    repo: KPIMeasurementUnitRepository = Depends(get_kpi_measurement_unit_repository),
    db: AsyncSession = Depends(get_db),
):
    updated = await repo.update(
        unit_id, name=data.name, description=data.description, sort_order=data.sort_order
    )
    if updated is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="KPI measurement unit not found")
    return KPIMeasurementUnitResponse.model_validate(updated)


@router.post("/{unit_id}/active", response_model=KPIMeasurementUnitResponse)
@transactional()
async def set_kpi_measurement_unit_active(
    unit_id: str,
    is_active: bool = Query(..., description="Activate or retire the row"),
    _user: TokenData = Depends(require_platform_admin),
    repo: KPIMeasurementUnitRepository = Depends(get_kpi_measurement_unit_repository),
    db: AsyncSession = Depends(get_db),
):
    updated = await repo.set_active(unit_id, is_active=is_active)
    if updated is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="KPI measurement unit not found")
    return KPIMeasurementUnitResponse.model_validate(updated)
