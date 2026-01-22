"""Activity API Routes - FastAPI routes for Activity operations."""

from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import get_activity_repository
from app.api.schemas.activity_schemas import (
    ActivityCreate,
    ActivityListResponse,
    ActivityResponse,
    ActivityUpdate,
)
from app.application.use_cases.activity_use_cases import (
    CreateActivityUseCase,
    GetActivityUseCase,
    UpdateActivityUseCase,
)
from app.core.database import get_db
from app.domain.entities.activity import ActivityEntity
from app.domain.exceptions import DomainError
from app.domain.repositories.activity_repository import ActivityRepository
from app.domain.value_objects.core import ActivityId, TenantId, UserId
from app.shared.utils.generators import generate_cuid
from app.shared.utils.http_errors import get_error_status_code

router = APIRouter(prefix="/activities", tags=["activities"])


def _to_activity_response(activity: ActivityEntity) -> ActivityResponse:
    """Map ActivityEntity to API response."""
    return ActivityResponse(
        id=activity._id.value,
        tenant_id=activity._tenant_id.value,
        client_id=activity._client_id,
        activity_type=activity._activity_type,
        subject=activity._subject,
        description=activity._description,
        outcome=activity._outcome,
        created_by=activity._created_by.value,
        occurred_at=activity._occurred_at.isoformat(),
        next_follow_up=activity._next_follow_up.isoformat() if activity._next_follow_up else None,
        is_important=activity._is_important,
        created_at=activity._created_at.isoformat(),
        updated_at=activity._updated_at.isoformat(),
    )


@router.post(
    "/",
    response_model=ActivityResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new activity",
)
async def create_activity(
    data: ActivityCreate,
    tenant_id: str = Query(..., description="Tenant identifier"),
    created_by: str = Query(..., description="User ID who created the activity"),
    activity_repo: ActivityRepository = Depends(get_activity_repository),
    db: AsyncSession = Depends(get_db),
):
    """Create a new activity."""
    try:
        create_use_case = CreateActivityUseCase(activity_repo)
        activity = await create_use_case.execute(
            activity_id=ActivityId(generate_cuid()),
            tenant_id=TenantId(tenant_id),
            client_id=data.client_id,
            activity_type=data.activity_type,
            description=data.description,
            created_by=UserId(created_by),
            subject=data.subject,
            outcome=data.outcome,
            occurred_at=data.occurred_at,
            next_follow_up=data.next_follow_up,
            is_important=data.is_important,
        )
        await db.commit()
        return _to_activity_response(activity)
    except ValueError as e:
        await db.rollback()
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)) from e
    except DomainError as e:
        await db.rollback()
        status_code = get_error_status_code(str(e))
        raise HTTPException(status_code=status_code, detail=str(e)) from e


@router.patch(
    "/{activity_id}",
    response_model=ActivityResponse,
    summary="Update an activity",
)
async def update_activity(
    activity_id: str,
    data: ActivityUpdate,
    activity_repo: ActivityRepository = Depends(get_activity_repository),
    db: AsyncSession = Depends(get_db),
):
    """Update an activity."""
    try:
        update_use_case = UpdateActivityUseCase(activity_repo)
        activity = await update_use_case.execute(
            ActivityId(activity_id),
            description=data.description,
            outcome=data.outcome,
            next_follow_up=data.next_follow_up,
            is_important=data.is_important,
        )
        await db.commit()
        return _to_activity_response(activity)
    except ValueError as e:
        await db.rollback()
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)) from e
    except DomainError as e:
        await db.rollback()
        status_code = get_error_status_code(str(e))
        raise HTTPException(status_code=status_code, detail=str(e)) from e


@router.get(
    "/",
    response_model=ActivityListResponse,
    summary="List activities with filtering and pagination",
)
async def list_activities(
    tenant_id: str = Query(..., description="Tenant identifier"),
    client_id: str | None = Query(None, description="Filter by client"),
    activity_type: str | None = Query(None, description="Filter by activity type"),
    created_by: str | None = Query(None, description="Filter by creator"),
    date_from: datetime | None = Query(None, description="Filter from date"),
    date_to: datetime | None = Query(None, description="Filter to date"),
    is_important: bool | None = Query(None, description="Filter by important status"),
    search: str | None = Query(None, description="Search in description or subject"),
    page: int = Query(1, ge=1, description="Page number"),
    limit: int = Query(20, ge=1, le=100, description="Items per page"),
    activity_repo: ActivityRepository = Depends(get_activity_repository),
):
    """List activities with filtering, searching, and pagination."""
    offset = (page - 1) * limit

    activities = await activity_repo.list_all(
        tenant_id=TenantId(tenant_id),
        client_id=client_id,
        activity_type=activity_type,
        created_by=created_by,
        date_from=date_from,
        date_to=date_to,
        is_important=is_important,
        search=search,
        limit=limit,
        offset=offset,
    )

    total = await activity_repo.count(
        tenant_id=TenantId(tenant_id),
        client_id=client_id,
        activity_type=activity_type,
        created_by=created_by,
        date_from=date_from,
        date_to=date_to,
        is_important=is_important,
        search=search,
    )

    activity_responses = [_to_activity_response(activity) for activity in activities]

    return ActivityListResponse(
        items=activity_responses,
        total=total,
        page=page,
        limit=limit,
        has_more=(offset + limit) < total,
    )


@router.get(
    "/{activity_id}",
    response_model=ActivityResponse,
    summary="Get activity by ID",
)
async def get_activity(
    activity_id: str,
    activity_repo: ActivityRepository = Depends(get_activity_repository),
):
    """Get activity by ID."""
    get_use_case = GetActivityUseCase(activity_repo)
    activity = await get_use_case.execute(ActivityId(activity_id))
    if not activity:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Activity not found")
    return _to_activity_response(activity)


@router.get(
    "/client/{client_id}",
    response_model=ActivityListResponse,
    summary="Get all activities for a client",
)
async def get_activities_by_client(
    client_id: str,
    tenant_id: str = Query(..., description="Tenant identifier"),
    activity_repo: ActivityRepository = Depends(get_activity_repository),
):
    """Get all activities for a specific client."""
    activities = await activity_repo.get_by_client_id(client_id, TenantId(tenant_id))
    activity_responses = [_to_activity_response(activity) for activity in activities]
    return ActivityListResponse(
        items=activity_responses,
        total=len(activity_responses),
        page=1,
        limit=len(activity_responses),
        has_more=False,
    )
