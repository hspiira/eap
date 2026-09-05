"""Diagnosis taxonomy routes (Phase 2 #D-Tax)."""

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import get_diagnosis_repository
from app.api.schemas.diagnosis_schemas import (
    DiagnosisResponse,
    DiagnosisTreeResponse,
    DiagnosisTypeResponse,
    DiagnosisTypeWithChildrenResponse,
)
from app.core.database import get_db
from app.core.security import TokenData, get_current_user
from app.domain.repositories.diagnosis_repository import DiagnosisRepository
from app.shared.decorators import readonly

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
