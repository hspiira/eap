"""Presenting problem taxonomy routes.

Replaces the ``PresentingProblem`` enum, whose explicit ``OTHER`` member was
already evidence the fixed list was insufficient: a new value is now a row an
operator adds through this API, not a code deploy.
"""

from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import get_presenting_problem_repository
from app.api.dependencies.audit import get_audit_event_handler
from app.api.schemas.presenting_problem_schemas import (
    PresentingProblemCreate,
    PresentingProblemResponse,
    PresentingProblemUpdate,
)
from app.core.authorization import require_platform_admin
from app.core.database import get_db
from app.core.reference_cache import cached_lookup, invalidate_reference_cache
from app.core.security import TokenData, get_current_user
from app.domain.enums import AuditActionType
from app.domain.repositories.presenting_problem_repository import (
    PresentingProblemRepository,
)
from app.shared.decorators import readonly, transactional
from app.shared.utils.route_audit_helper import audit_reference_change

router = APIRouter(prefix="/presenting-problems", tags=["presenting-problems"])

_RESOURCE = "presenting_problems"


@router.get("", response_model=list[PresentingProblemResponse], summary="List presenting problems")
@readonly()
@cached_lookup(_RESOURCE)
async def list_presenting_problems(
    active_only: bool = Query(True, description="Return only active rows"),
    _user: TokenData = Depends(get_current_user),
    repo: PresentingProblemRepository = Depends(get_presenting_problem_repository),
    db: AsyncSession = Depends(get_db),
):
    problems = await repo.list_all(active_only=active_only)
    return [PresentingProblemResponse.model_validate(p) for p in problems]


@router.post("", response_model=PresentingProblemResponse, status_code=status.HTTP_201_CREATED)
@transactional()
async def create_presenting_problem(
    data: PresentingProblemCreate,
    request: Request,
    _user: TokenData = Depends(require_platform_admin),
    repo: PresentingProblemRepository = Depends(get_presenting_problem_repository),
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
        resource_type="PresentingProblem",
        resource_id=created.id,
        after=created,
    )
    await invalidate_reference_cache(_RESOURCE)
    return PresentingProblemResponse.model_validate(created)


@router.patch("/{problem_id}", response_model=PresentingProblemResponse)
@transactional()
async def update_presenting_problem(
    problem_id: str,
    data: PresentingProblemUpdate,
    request: Request,
    _user: TokenData = Depends(require_platform_admin),
    repo: PresentingProblemRepository = Depends(get_presenting_problem_repository),
    audit_handler=Depends(get_audit_event_handler),
    db: AsyncSession = Depends(get_db),
):
    before = await repo.get_by_id(problem_id)
    updated = await repo.update(
        problem_id, name=data.name, description=data.description, sort_order=data.sort_order
    )
    if updated is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Presenting problem not found")
    await audit_reference_change(
        audit_handler,
        _user,
        request,
        action=AuditActionType.UPDATE,
        resource_type="PresentingProblem",
        resource_id=updated.id,
        before=before,
        after=updated,
    )
    await invalidate_reference_cache(_RESOURCE)
    return PresentingProblemResponse.model_validate(updated)


@router.post("/{problem_id}/active", response_model=PresentingProblemResponse)
@transactional()
async def set_presenting_problem_active(
    problem_id: str,
    request: Request,
    is_active: bool = Query(..., description="Activate or retire the row"),
    _user: TokenData = Depends(require_platform_admin),
    repo: PresentingProblemRepository = Depends(get_presenting_problem_repository),
    audit_handler=Depends(get_audit_event_handler),
    db: AsyncSession = Depends(get_db),
):
    before = await repo.get_by_id(problem_id)
    updated = await repo.set_active(problem_id, is_active=is_active)
    if updated is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Presenting problem not found")
    await audit_reference_change(
        audit_handler,
        _user,
        request,
        action=AuditActionType.UPDATE,
        resource_type="PresentingProblem",
        resource_id=updated.id,
        before=before,
        after=updated,
    )
    await invalidate_reference_cache(_RESOURCE)
    return PresentingProblemResponse.model_validate(updated)
