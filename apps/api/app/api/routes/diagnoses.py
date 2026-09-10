"""Diagnosis taxonomy routes (Phase 2 #D-Tax)."""

from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import get_diagnosis_repository
from app.api.dependencies.audit import get_audit_event_handler
from app.api.schemas.diagnosis_schemas import (
    DiagnosisAliasResponse,
    DiagnosisAliasUpsert,
    DiagnosisCapabilitiesResponse,
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
from app.core.authorization import (
    is_platform_admin,
    require_platform_admin,
    require_tenant_role,
)
from app.core.database import get_db
from app.core.security import TokenData, get_current_user
from app.domain.entities.diagnosis import DiagnosisAlias, TenantOverlay
from app.domain.enums import AliasConfidence, AuditActionType, TenantRole
from app.domain.repositories.diagnosis_repository import DiagnosisRepository
from app.domain.services.diagnosis_alias import normalise_diagnosis_value
from app.shared.decorators import readonly, transactional
from app.shared.utils.route_audit_helper import audit_reference_change

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
    user: TokenData = Depends(get_current_user),
    repo: DiagnosisRepository = Depends(get_diagnosis_repository),
    db: AsyncSession = Depends(get_db),
):
    types = await repo.list_types(active_only=active_only)
    diagnoses = await repo.list_diagnoses(active_only=active_only)
    overlay = await repo.tenant_overlay(user.tenant_id)
    return DiagnosisTreeResponse(types=_build_tree(types, diagnoses, overlay))


def _visible(overlay: dict, type_id: str, diagnosis_id: str | None) -> bool:
    row = overlay.get((type_id, diagnosis_id))
    return True if row is None else row.is_enabled


def _label(overlay: dict, type_id: str, diagnosis_id: str | None, default: str) -> str:
    row = overlay.get((type_id, diagnosis_id))
    return row.local_label if row is not None and row.local_label else default


def _order(overlay: dict, type_id: str, diagnosis_id: str | None, default: int) -> int:
    row = overlay.get((type_id, diagnosis_id))
    if row is None or row.sort_order is None:
        return default
    return row.sort_order


def _children(diagnoses, type_id: str, overlay: dict) -> list[DiagnosisResponse]:
    rows = [
        DiagnosisResponse(
            id=d.id,
            type_id=d.type_id,
            code=d.code,
            name=_label(overlay, d.type_id, d.id, d.name),
            description=d.description,
            sort_order=_order(overlay, d.type_id, d.id, d.sort_order),
        )
        for d in diagnoses
        if d.type_id == type_id and _visible(overlay, d.type_id, d.id)
    ]
    return sorted(rows, key=lambda r: (r.sort_order, r.name))


def _build_tree(types, diagnoses, overlay: dict) -> list[DiagnosisTypeWithChildrenResponse]:
    """Apply the tenant overlay to the shared taxonomy without mutating it."""
    rows = [
        DiagnosisTypeWithChildrenResponse(
            id=t.id,
            code=t.code,
            name=_label(overlay, t.id, None, t.name),
            description=t.description,
            sort_order=_order(overlay, t.id, None, t.sort_order),
            diagnoses=_children(diagnoses, t.id, overlay),
        )
        for t in types
        if _visible(overlay, t.id, None)
    ]
    return sorted(rows, key=lambda r: (r.sort_order, r.name))


def _found(entity, label: str):
    if entity is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"{label} not found")
    return entity


async def _assert_available_type(repo: DiagnosisRepository, type_id: str) -> None:
    """Reject a move onto a type the tree would not return.

    ``list_types`` requires ``is_active`` and a null ``effective_until``, so a
    move onto a retired type would take the diagnosis out of every picker while
    reporting success.
    """
    target = _found(await repo.get_type_by_id(type_id), "Diagnosis type")
    if not target.is_active or target.effective_until is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Diagnosis type is retired; activate it before moving a diagnosis under it",
        )


# === Taxonomy writes (platform admin) ===


@router.post("/types", response_model=DiagnosisTypeResponse, status_code=status.HTTP_201_CREATED)
@transactional()
async def create_diagnosis_type(
    data: DiagnosisTypeCreate,
    request: Request,
    _user: TokenData = Depends(require_platform_admin),
    repo: DiagnosisRepository = Depends(get_diagnosis_repository),
    audit_handler=Depends(get_audit_event_handler),
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
    await audit_reference_change(
        audit_handler,
        _user,
        request,
        action=AuditActionType.CREATE,
        resource_type="DiagnosisType",
        resource_id=created.id,
        after=created,
    )
    return DiagnosisTypeResponse.model_validate(created)


@router.patch("/types/{type_id}", response_model=DiagnosisTypeResponse)
@transactional()
async def update_diagnosis_type(
    type_id: str,
    data: DiagnosisTypeUpdate,
    request: Request,
    _user: TokenData = Depends(require_platform_admin),
    repo: DiagnosisRepository = Depends(get_diagnosis_repository),
    audit_handler=Depends(get_audit_event_handler),
    db: AsyncSession = Depends(get_db),
):
    before = await repo.get_type_by_id(type_id)
    updated = _found(
        await repo.update_type(
            type_id, name=data.name, description=data.description, sort_order=data.sort_order
        ),
        "Diagnosis type",
    )
    await audit_reference_change(
        audit_handler,
        _user,
        request,
        action=AuditActionType.UPDATE,
        resource_type="DiagnosisType",
        resource_id=updated.id,
        before=before,
        after=updated,
    )
    return DiagnosisTypeResponse.model_validate(updated)


@router.post("/types/{type_id}/active", response_model=DiagnosisTypeResponse)
@transactional()
async def set_diagnosis_type_active(
    type_id: str,
    request: Request,
    is_active: bool = Query(..., description="Activate or retire the type"),
    _user: TokenData = Depends(require_platform_admin),
    repo: DiagnosisRepository = Depends(get_diagnosis_repository),
    audit_handler=Depends(get_audit_event_handler),
    db: AsyncSession = Depends(get_db),
):
    before = await repo.get_type_by_id(type_id)
    updated = _found(await repo.set_type_active(type_id, is_active=is_active), "Diagnosis type")
    await audit_reference_change(
        audit_handler,
        _user,
        request,
        action=AuditActionType.UPDATE,
        resource_type="DiagnosisType",
        resource_id=updated.id,
        before=before,
        after=updated,
    )
    return DiagnosisTypeResponse.model_validate(updated)


@router.post("", response_model=DiagnosisResponse, status_code=status.HTTP_201_CREATED)
@transactional()
async def create_diagnosis(
    data: DiagnosisCreate,
    request: Request,
    _user: TokenData = Depends(require_platform_admin),
    repo: DiagnosisRepository = Depends(get_diagnosis_repository),
    audit_handler=Depends(get_audit_event_handler),
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
    await audit_reference_change(
        audit_handler,
        _user,
        request,
        action=AuditActionType.CREATE,
        resource_type="Diagnosis",
        resource_id=created.id,
        after=created,
    )
    return DiagnosisResponse.model_validate(created)


@router.patch("/{diagnosis_id}", response_model=DiagnosisResponse)
@transactional()
async def update_diagnosis(
    diagnosis_id: str,
    data: DiagnosisUpdate,
    request: Request,
    _user: TokenData = Depends(require_platform_admin),
    repo: DiagnosisRepository = Depends(get_diagnosis_repository),
    audit_handler=Depends(get_audit_event_handler),
    db: AsyncSession = Depends(get_db),
):
    if data.type_id is not None:
        await _assert_available_type(repo, data.type_id)
    before = await repo.get_diagnosis_by_id(diagnosis_id)
    updated = _found(
        await repo.update_diagnosis(
            diagnosis_id,
            type_id=data.type_id,
            name=data.name,
            description=data.description,
            sort_order=data.sort_order,
        ),
        "Diagnosis",
    )
    await audit_reference_change(
        audit_handler,
        _user,
        request,
        action=AuditActionType.UPDATE,
        resource_type="Diagnosis",
        resource_id=updated.id,
        before=before,
        after=updated,
    )
    return DiagnosisResponse.model_validate(updated)


@router.post("/{diagnosis_id}/active", response_model=DiagnosisResponse)
@transactional()
async def set_diagnosis_active(
    diagnosis_id: str,
    request: Request,
    is_active: bool = Query(..., description="Activate or retire the diagnosis"),
    _user: TokenData = Depends(require_platform_admin),
    repo: DiagnosisRepository = Depends(get_diagnosis_repository),
    audit_handler=Depends(get_audit_event_handler),
    db: AsyncSession = Depends(get_db),
):
    before = await repo.get_diagnosis_by_id(diagnosis_id)
    updated = _found(
        await repo.set_diagnosis_active(diagnosis_id, is_active=is_active), "Diagnosis"
    )
    await audit_reference_change(
        audit_handler,
        _user,
        request,
        action=AuditActionType.UPDATE,
        resource_type="Diagnosis",
        resource_id=updated.id,
        before=before,
        after=updated,
    )
    return DiagnosisResponse.model_validate(updated)


@router.get("/capabilities", response_model=DiagnosisCapabilitiesResponse)
@readonly()
async def diagnosis_capabilities(
    user: TokenData = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return DiagnosisCapabilitiesResponse(
        can_manage_taxonomy=is_platform_admin(user),
        can_manage_overlay=user.role == TenantRole.ADMIN.value,
    )


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


def _overlay_id(overlay: TenantOverlay) -> str:
    """The overlay row carries no id of its own; it is keyed by what it overlays."""
    return f"{overlay.diagnosis_type_id}:{overlay.diagnosis_id or ''}"


@router.put("/settings", response_model=DiagnosisOverlayResponse)
@transactional()
async def set_diagnosis_setting(
    data: DiagnosisOverlayUpdate,
    request: Request,
    user: TokenData = Depends(require_tenant_role(TenantRole.ADMIN)),
    repo: DiagnosisRepository = Depends(get_diagnosis_repository),
    audit_handler=Depends(get_audit_event_handler),
    db: AsyncSession = Depends(get_db),
):
    overlay = await repo.tenant_overlay(user.tenant_id)
    before = overlay.get((data.diagnosis_type_id, data.diagnosis_id))
    saved = await repo.set_tenant_overlay(
        user.tenant_id,
        diagnosis_type_id=data.diagnosis_type_id,
        diagnosis_id=data.diagnosis_id,
        is_enabled=data.is_enabled,
        sort_order=data.sort_order,
        local_label=data.local_label,
    )
    await audit_reference_change(
        audit_handler,
        user,
        request,
        action=AuditActionType.UPDATE if before is not None else AuditActionType.CREATE,
        resource_type="DiagnosisSetting",
        resource_id=_overlay_id(saved),
        before=before,
        after=saved,
        tenant_id=user.tenant_id,
    )
    return DiagnosisOverlayResponse.model_validate(saved)


# === Legacy aliases (platform admin) ===
#
# Aliases exist because free-text diagnosis spellings keep arriving from the
# field. Adding one used to mean writing an Alembic migration, which is why
# values awaiting a clinical decision stayed unmapped and their rows kept
# failing the import. These routes let the taxonomy owner resolve a value
# without a deploy.


@router.get("/aliases", response_model=list[DiagnosisAliasResponse])
@readonly()
async def list_diagnosis_aliases(
    confidence: AliasConfidence | None = Query(
        None, description="Filter to mappings still awaiting sign-off, or those confirmed"
    ),
    _user: TokenData = Depends(require_platform_admin),
    repo: DiagnosisRepository = Depends(get_diagnosis_repository),
    db: AsyncSession = Depends(get_db),
):
    aliases = await repo.list_aliases(confidence=confidence.value if confidence else None)
    return [DiagnosisAliasResponse.model_validate(a) for a in aliases]


async def _alias_for(repo: DiagnosisRepository, raw_value: str) -> DiagnosisAlias | None:
    """The alias a raw value already resolves to, matched on its normalised key."""
    key = normalise_diagnosis_value(raw_value)
    return next((a for a in await repo.list_aliases() if a.normalised_key == key), None)


@router.put("/aliases", response_model=DiagnosisAliasResponse)
@transactional()
async def upsert_diagnosis_alias(
    data: DiagnosisAliasUpsert,
    request: Request,
    _user: TokenData = Depends(require_platform_admin),
    repo: DiagnosisRepository = Depends(get_diagnosis_repository),
    audit_handler=Depends(get_audit_event_handler),
    db: AsyncSession = Depends(get_db),
):
    """Map a legacy spelling onto the taxonomy, keyed on its normalised form."""
    # An alias pointing at a row that does not exist would fail the import it
    # was meant to unblock, so the reference is checked here rather than at
    # import time.
    types = await repo.list_types(active_only=False)
    if not any(t.id == data.diagnosis_type_id for t in types):
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Diagnosis type not found")
    if data.diagnosis_id is not None:
        diagnoses = await repo.list_diagnoses(active_only=False)
        target = next((d for d in diagnoses if d.id == data.diagnosis_id), None)
        if target is None:
            raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Diagnosis not found")
        if target.type_id != data.diagnosis_type_id:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
                detail="Diagnosis does not belong to the given type",
            )
    before = await _alias_for(repo, data.raw_value)
    saved = await repo.upsert_alias(
        raw_value=data.raw_value,
        diagnosis_type_id=data.diagnosis_type_id,
        diagnosis_id=data.diagnosis_id,
        source=data.source,
        confidence=data.confidence.value,
    )
    await audit_reference_change(
        audit_handler,
        _user,
        request,
        action=AuditActionType.UPDATE if before is not None else AuditActionType.CREATE,
        resource_type="DiagnosisAlias",
        resource_id=saved.id,
        before=before,
        after=saved,
    )
    return DiagnosisAliasResponse.model_validate(saved)
