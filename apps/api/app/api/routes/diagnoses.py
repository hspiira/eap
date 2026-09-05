"""Diagnosis taxonomy routes (Phase 2 #D-Tax)."""

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import get_diagnosis_repository
from app.api.schemas.diagnosis_schemas import (
    DiagnosisCreate,
    DiagnosisOverlayResponse,
    DiagnosisOverlayUpdate,
    DiagnosisResponse,
    DiagnosisTreeResponse,
    DiagnosisTypeCreate,
    DiagnosisTypeResponse,
    DiagnosisTypeUpdate,
    DiagnosisTypeWithChildrenResponse,
    DiagnosisUpdate,
)
from app.core.authorization import require_platform_admin, require_tenant_role
from app.core.database import get_db
from app.core.security import TokenData, get_current_user
from app.domain.enums import TenantRole
from app.domain.repositories.diagnosis_repository import DiagnosisRepository
from app.shared.decorators import readonly, transactional

router = APIRouter(prefix="/diagnoses", tags=["diagnoses"])


@router.get(
    "/types",
    response_model=list[DiagnosisTypeResponse],
    summary="List diagnosis types",
)
@readonly()
async def list_diagnosis_types(
    active_only: bool = Query(True, description="Return only active types"),
    _user: TokenData = Depends(get_current_user),
    repo: DiagnosisRepository = Depends(get_diagnosis_repository),
    db: AsyncSession = Depends(get_db),
):
    types = await repo.list_types(active_only=active_only)
    return [DiagnosisTypeResponse.model_validate(t) for t in types]


@router.get(
    "",
    response_model=list[DiagnosisResponse],
    summary="List diagnoses, optionally filtered by type",
)
@readonly()
async def list_diagnoses(
    type_code: str | None = Query(None, description="Filter to a single type code"),
    active_only: bool = Query(True, description="Return only active diagnoses"),
    _user: TokenData = Depends(get_current_user),
    repo: DiagnosisRepository = Depends(get_diagnosis_repository),
    db: AsyncSession = Depends(get_db),
):
    diagnoses = await repo.list_diagnoses(type_code=type_code, active_only=active_only)
    return [DiagnosisResponse.model_validate(d) for d in diagnoses]


@router.get(
    "/tree",
    response_model=DiagnosisTreeResponse,
    summary="Hierarchical diagnosis selector (types with nested diagnoses)",
)
@readonly()
async def diagnosis_tree(
    active_only: bool = Query(True, description="Return only active rows"),
    _user: TokenData = Depends(get_current_user),
    repo: DiagnosisRepository = Depends(get_diagnosis_repository),
    db: AsyncSession = Depends(get_db),
):
    types = await repo.list_types(active_only=active_only)
    diagnoses = await repo.list_diagnoses(active_only=active_only)
    by_type: dict[str, list[DiagnosisResponse]] = {}
    for d in diagnoses:
        by_type.setdefault(d.type_id, []).append(DiagnosisResponse.model_validate(d))
    return DiagnosisTreeResponse(
        types=[
            DiagnosisTypeWithChildrenResponse(
                id=t.id,
                code=t.code,
                name=t.name,
                description=t.description,
                sort_order=t.sort_order,
                diagnoses=by_type.get(t.id, []),
            )
            for t in types
        ]
    )


def _found(entity, label: str):
    if entity is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"{label} not found")
    return entity


# === Taxonomy writes (platform admin) ===


@router.post("/types", response_model=DiagnosisTypeResponse, status_code=status.HTTP_201_CREATED)
@transactional()
async def create_diagnosis_type(
    data: DiagnosisTypeCreate,
    _user: TokenData = Depends(require_platform_admin),
    repo: DiagnosisRepository = Depends(get_diagnosis_repository),
    db: AsyncSession = Depends(get_db),
):
    if await repo.get_type_by_code(data.code):
        raise HTTPException(status.HTTP_409_CONFLICT, detail="Type code already exists")
    created = await repo.create_type(
        code=data.code,
        name=data.name,
        description=data.description,
        sort_order=data.sort_order,
    )
    return DiagnosisTypeResponse.model_validate(created)


@router.patch("/types/{type_id}", response_model=DiagnosisTypeResponse)
@transactional()
async def update_diagnosis_type(
    type_id: str,
    data: DiagnosisTypeUpdate,
    _user: TokenData = Depends(require_platform_admin),
    repo: DiagnosisRepository = Depends(get_diagnosis_repository),
    db: AsyncSession = Depends(get_db),
):
    updated = await repo.update_type(
        type_id, name=data.name, description=data.description, sort_order=data.sort_order
    )
    return DiagnosisTypeResponse.model_validate(_found(updated, "Diagnosis type"))


@router.post("/types/{type_id}/active", response_model=DiagnosisTypeResponse)
@transactional()
async def set_diagnosis_type_active(
    type_id: str,
    is_active: bool = Query(..., description="Activate or retire the type"),
    _user: TokenData = Depends(require_platform_admin),
    repo: DiagnosisRepository = Depends(get_diagnosis_repository),
    db: AsyncSession = Depends(get_db),
):
    updated = await repo.set_type_active(type_id, is_active=is_active)
    return DiagnosisTypeResponse.model_validate(_found(updated, "Diagnosis type"))


@router.post("", response_model=DiagnosisResponse, status_code=status.HTTP_201_CREATED)
@transactional()
async def create_diagnosis(
    data: DiagnosisCreate,
    _user: TokenData = Depends(require_platform_admin),
    repo: DiagnosisRepository = Depends(get_diagnosis_repository),
    db: AsyncSession = Depends(get_db),
):
    if await repo.get_diagnosis_by_code(data.code):
        raise HTTPException(status.HTTP_409_CONFLICT, detail="Diagnosis code already exists")
    created = await repo.create_diagnosis(
        type_id=data.type_id,
        code=data.code,
        name=data.name,
        description=data.description,
        sort_order=data.sort_order,
    )
    return DiagnosisResponse.model_validate(created)


@router.patch("/{diagnosis_id}", response_model=DiagnosisResponse)
@transactional()
async def update_diagnosis(
    diagnosis_id: str,
    data: DiagnosisUpdate,
    _user: TokenData = Depends(require_platform_admin),
    repo: DiagnosisRepository = Depends(get_diagnosis_repository),
    db: AsyncSession = Depends(get_db),
):
    updated = await repo.update_diagnosis(
        diagnosis_id, name=data.name, description=data.description, sort_order=data.sort_order
    )
    return DiagnosisResponse.model_validate(_found(updated, "Diagnosis"))


@router.post("/{diagnosis_id}/active", response_model=DiagnosisResponse)
@transactional()
async def set_diagnosis_active(
    diagnosis_id: str,
    is_active: bool = Query(..., description="Activate or retire the diagnosis"),
    _user: TokenData = Depends(require_platform_admin),
    repo: DiagnosisRepository = Depends(get_diagnosis_repository),
    db: AsyncSession = Depends(get_db),
):
    updated = await repo.set_diagnosis_active(diagnosis_id, is_active=is_active)
    return DiagnosisResponse.model_validate(_found(updated, "Diagnosis"))


# === Tenant overlay (tenant admin) ===


@router.get("/settings", response_model=list[DiagnosisOverlayResponse])
@readonly()
async def list_diagnosis_settings(
    user: TokenData = Depends(get_current_user),
    repo: DiagnosisRepository = Depends(get_diagnosis_repository),
    db: AsyncSession = Depends(get_db),
):
    overlay = await repo.tenant_overlay(user.tenant_id)
    return [DiagnosisOverlayResponse.model_validate(o) for o in overlay.values()]


@router.put("/settings", response_model=DiagnosisOverlayResponse)
@transactional()
async def set_diagnosis_setting(
    data: DiagnosisOverlayUpdate,
    user: TokenData = Depends(require_tenant_role(TenantRole.ADMIN)),
    repo: DiagnosisRepository = Depends(get_diagnosis_repository),
    db: AsyncSession = Depends(get_db),
):
    saved = await repo.set_tenant_overlay(
        user.tenant_id,
        diagnosis_type_id=data.diagnosis_type_id,
        diagnosis_id=data.diagnosis_id,
        is_enabled=data.is_enabled,
        sort_order=data.sort_order,
        local_label=data.local_label,
    )
    return DiagnosisOverlayResponse.model_validate(saved)
