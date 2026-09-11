"""Case referral source taxonomy routes.

Replaces the ``CaseReferralSource`` enum: a new value is now a row an
operator adds through this API, not a code deploy.
"""

from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import get_case_referral_source_repository
from app.api.dependencies.audit import get_audit_event_handler
from app.api.schemas.case_referral_source_schemas import (
    CaseReferralSourceCreate,
    CaseReferralSourceResponse,
    CaseReferralSourceUpdate,
)
from app.core.authorization import require_platform_admin
from app.core.database import get_db
from app.core.reference_cache import cached_lookup, invalidate_reference_cache
from app.core.security import TokenData, get_current_user
from app.domain.enums import AuditActionType
from app.domain.repositories.case_referral_source_repository import (
    CaseReferralSourceRepository,
)
from app.shared.decorators import readonly, transactional
from app.shared.utils.route_audit_helper import audit_reference_change

router = APIRouter(prefix="/case-referral-sources", tags=["case-referral-sources"])

_RESOURCE = "case_referral_sources"


@router.get(
    "", response_model=list[CaseReferralSourceResponse], summary="List case referral sources"
)
@readonly()
@cached_lookup(_RESOURCE)
async def list_case_referral_sources(
    active_only: bool = Query(True, description="Return only active rows"),
    _user: TokenData = Depends(get_current_user),
    repo: CaseReferralSourceRepository = Depends(get_case_referral_source_repository),
    db: AsyncSession = Depends(get_db),
):
    sources = await repo.list_all(active_only=active_only)
    return [CaseReferralSourceResponse.model_validate(s) for s in sources]


@router.post("", response_model=CaseReferralSourceResponse, status_code=status.HTTP_201_CREATED)
@transactional()
async def create_case_referral_source(
    data: CaseReferralSourceCreate,
    request: Request,
    _user: TokenData = Depends(require_platform_admin),
    repo: CaseReferralSourceRepository = Depends(get_case_referral_source_repository),
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
        resource_type="CaseReferralSource",
        resource_id=created.id,
        after=created,
    )
    await invalidate_reference_cache(_RESOURCE)
    return CaseReferralSourceResponse.model_validate(created)


@router.patch("/{source_id}", response_model=CaseReferralSourceResponse)
@transactional()
async def update_case_referral_source(
    source_id: str,
    data: CaseReferralSourceUpdate,
    request: Request,
    _user: TokenData = Depends(require_platform_admin),
    repo: CaseReferralSourceRepository = Depends(get_case_referral_source_repository),
    audit_handler=Depends(get_audit_event_handler),
    db: AsyncSession = Depends(get_db),
):
    before = await repo.get_by_id(source_id)
    updated = await repo.update(
        source_id, name=data.name, description=data.description, sort_order=data.sort_order
    )
    if updated is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Case referral source not found")
    await audit_reference_change(
        audit_handler,
        _user,
        request,
        action=AuditActionType.UPDATE,
        resource_type="CaseReferralSource",
        resource_id=updated.id,
        before=before,
        after=updated,
    )
    await invalidate_reference_cache(_RESOURCE)
    return CaseReferralSourceResponse.model_validate(updated)


@router.post("/{source_id}/active", response_model=CaseReferralSourceResponse)
@transactional()
async def set_case_referral_source_active(
    source_id: str,
    request: Request,
    is_active: bool = Query(..., description="Activate or retire the row"),
    _user: TokenData = Depends(require_platform_admin),
    repo: CaseReferralSourceRepository = Depends(get_case_referral_source_repository),
    audit_handler=Depends(get_audit_event_handler),
    db: AsyncSession = Depends(get_db),
):
    before = await repo.get_by_id(source_id)
    updated = await repo.set_active(source_id, is_active=is_active)
    if updated is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Case referral source not found")
    await audit_reference_change(
        audit_handler,
        _user,
        request,
        action=AuditActionType.UPDATE,
        resource_type="CaseReferralSource",
        resource_id=updated.id,
        before=before,
        after=updated,
    )
    await invalidate_reference_cache(_RESOURCE)
    return CaseReferralSourceResponse.model_validate(updated)
