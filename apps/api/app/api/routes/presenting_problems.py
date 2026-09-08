"""Presenting problem taxonomy routes.

Replaces the ``PresentingProblem`` enum, whose explicit ``OTHER`` member was
already evidence the fixed list was insufficient: a new value is now a row an
operator adds through this API, not a code deploy.
"""

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import get_presenting_problem_repository
from app.api.schemas.presenting_problem_schemas import (
    PresentingProblemCreate,
    PresentingProblemResponse,
    PresentingProblemUpdate,
)
from app.core.authorization import require_platform_admin
from app.core.database import get_db
from app.core.security import TokenData, get_current_user
from app.domain.repositories.presenting_problem_repository import (
    PresentingProblemRepository,
)
from app.shared.decorators import readonly, transactional

router = APIRouter(prefix="/presenting-problems", tags=["presenting-problems"])


@router.get("", response_model=list[PresentingProblemResponse], summary="List presenting problems")
@readonly()
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
    _user: TokenData = Depends(require_platform_admin),
    repo: PresentingProblemRepository = Depends(get_presenting_problem_repository),
    db: AsyncSession = Depends(get_db),
):
    if await repo.get_by_code(data.code):
        raise HTTPException(status.HTTP_409_CONFLICT, detail="Code already exists")
    created = await repo.create(
        code=data.code, name=data.name, description=data.description, sort_order=data.sort_order
    )
    return PresentingProblemResponse.model_validate(created)


@router.patch("/{problem_id}", response_model=PresentingProblemResponse)
@transactional()
async def update_presenting_problem(
    problem_id: str,
    data: PresentingProblemUpdate,
    _user: TokenData = Depends(require_platform_admin),
    repo: PresentingProblemRepository = Depends(get_presenting_problem_repository),
    db: AsyncSession = Depends(get_db),
):
    updated = await repo.update(
        problem_id, name=data.name, description=data.description, sort_order=data.sort_order
    )
    if updated is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Presenting problem not found")
    return PresentingProblemResponse.model_validate(updated)


@router.post("/{problem_id}/active", response_model=PresentingProblemResponse)
@transactional()
async def set_presenting_problem_active(
    problem_id: str,
    is_active: bool = Query(..., description="Activate or retire the row"),
    _user: TokenData = Depends(require_platform_admin),
    repo: PresentingProblemRepository = Depends(get_presenting_problem_repository),
    db: AsyncSession = Depends(get_db),
):
    updated = await repo.set_active(problem_id, is_active=is_active)
    if updated is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Presenting problem not found")
    return PresentingProblemResponse.model_validate(updated)
