"""ClientTag API Routes - FastAPI routes for ClientTag operations."""

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import get_client_tag_repository
from app.api.schemas.client_tag_schemas import (
    ClientTagCreate,
    ClientTagListResponse,
    ClientTagResponse,
    ClientTagUpdate,
)
from app.application.use_cases.client_tag_use_cases import (
    ActivateClientTagUseCase,
    CreateClientTagUseCase,
    DeactivateClientTagUseCase,
    GetClientTagUseCase,
    UpdateClientTagUseCase,
)
from app.core.database import get_db
from app.domain.entities.client_tag import ClientTagEntity
from app.domain.exceptions import DomainError
from app.domain.repositories.client_tag_repository import ClientTagRepository
from app.domain.value_objects.core import ClientTagId, TenantId
from app.shared.utils.generators import generate_cuid
from app.shared.utils.http_errors import get_error_status_code

router = APIRouter(prefix="/client-tags", tags=["client-tags"])


def _to_client_tag_response(tag: ClientTagEntity) -> ClientTagResponse:
    """Map ClientTagEntity to API response."""
    return ClientTagResponse(
        id=tag._id.value,
        tenant_id=tag._tenant_id.value,
        name=tag._name,
        description=tag._description,
        color=tag._color,
        is_active=tag.is_active(),
        created_at=tag._created_at.isoformat(),
        updated_at=tag._updated_at.isoformat(),
    )


@router.post(
    "/",
    response_model=ClientTagResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new client tag",
)
async def create_client_tag(
    data: ClientTagCreate,
    tenant_id: str = Query(..., description="Tenant identifier"),
    tag_repo: ClientTagRepository = Depends(get_client_tag_repository),
    db: AsyncSession = Depends(get_db),
):
    """Create a new client tag."""
    try:
        create_use_case = CreateClientTagUseCase(tag_repo)
        tag = await create_use_case.execute(
            tag_id=ClientTagId(generate_cuid()),
            tenant_id=TenantId(tenant_id),
            name=data.name,
            description=data.description,
            color=data.color,
        )
        await db.commit()
        return _to_client_tag_response(tag)
    except ValueError as e:
        await db.rollback()
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)) from e
    except DomainError as e:
        await db.rollback()
        status_code = get_error_status_code(str(e))
        raise HTTPException(status_code=status_code, detail=str(e)) from e


@router.patch(
    "/{tag_id}",
    response_model=ClientTagResponse,
    summary="Update a client tag",
)
async def update_client_tag(
    tag_id: str,
    data: ClientTagUpdate,
    tag_repo: ClientTagRepository = Depends(get_client_tag_repository),
    db: AsyncSession = Depends(get_db),
):
    """Update a client tag."""
    try:
        update_use_case = UpdateClientTagUseCase(tag_repo)
        tag = await update_use_case.execute(
            ClientTagId(tag_id),
            name=data.name,
            description=data.description,
            color=data.color,
        )
        await db.commit()
        return _to_client_tag_response(tag)
    except ValueError as e:
        await db.rollback()
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)) from e
    except DomainError as e:
        await db.rollback()
        status_code = get_error_status_code(str(e))
        raise HTTPException(status_code=status_code, detail=str(e)) from e


@router.post(
    "/{tag_id}/activate",
    response_model=ClientTagResponse,
    summary="Activate a client tag",
)
async def activate_client_tag(
    tag_id: str,
    tag_repo: ClientTagRepository = Depends(get_client_tag_repository),
    db: AsyncSession = Depends(get_db),
):
    """Activate a client tag."""
    try:
        activate_use_case = ActivateClientTagUseCase(tag_repo)
        tag = await activate_use_case.execute(ClientTagId(tag_id))
        await db.commit()
        return _to_client_tag_response(tag)
    except ValueError as e:
        await db.rollback()
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e)) from e
    except DomainError as e:
        await db.rollback()
        status_code = get_error_status_code(str(e))
        raise HTTPException(status_code=status_code, detail=str(e)) from e


@router.post(
    "/{tag_id}/deactivate",
    response_model=ClientTagResponse,
    summary="Deactivate a client tag",
)
async def deactivate_client_tag(
    tag_id: str,
    tag_repo: ClientTagRepository = Depends(get_client_tag_repository),
    db: AsyncSession = Depends(get_db),
):
    """Deactivate a client tag."""
    try:
        deactivate_use_case = DeactivateClientTagUseCase(tag_repo)
        tag = await deactivate_use_case.execute(ClientTagId(tag_id))
        await db.commit()
        return _to_client_tag_response(tag)
    except ValueError as e:
        await db.rollback()
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e)) from e
    except DomainError as e:
        await db.rollback()
        status_code = get_error_status_code(str(e))
        raise HTTPException(status_code=status_code, detail=str(e)) from e


@router.get(
    "/",
    response_model=ClientTagListResponse,
    summary="List client tags with filtering and pagination",
)
async def list_client_tags(
    tenant_id: str = Query(..., description="Tenant identifier"),
    is_active: bool | None = Query(None, description="Filter by active status"),
    search: str | None = Query(None, description="Search in tag name"),
    page: int = Query(1, ge=1, description="Page number"),
    limit: int = Query(20, ge=1, le=100, description="Items per page"),
    tag_repo: ClientTagRepository = Depends(get_client_tag_repository),
):
    """List client tags with filtering, searching, and pagination."""
    offset = (page - 1) * limit

    tags = await tag_repo.list_all(
        tenant_id=TenantId(tenant_id),
        is_active=is_active,
        search=search,
        limit=limit,
        offset=offset,
    )

    total = await tag_repo.count(
        tenant_id=TenantId(tenant_id),
        is_active=is_active,
        search=search,
    )

    tag_responses = [_to_client_tag_response(tag) for tag in tags]

    return ClientTagListResponse(
        items=tag_responses,
        total=total,
        page=page,
        limit=limit,
        has_more=(offset + limit) < total,
    )


@router.get(
    "/{tag_id}",
    response_model=ClientTagResponse,
    summary="Get client tag by ID",
)
async def get_client_tag(
    tag_id: str,
    tag_repo: ClientTagRepository = Depends(get_client_tag_repository),
):
    """Get client tag by ID."""
    get_use_case = GetClientTagUseCase(tag_repo)
    tag = await get_use_case.execute(ClientTagId(tag_id))
    if not tag:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Tag not found")
    return _to_client_tag_response(tag)


@router.get(
    "/check-name/{name}",
    summary="Check if client tag name is available",
)
async def check_client_tag_name_availability(
    name: str,
    tenant_id: str = Query(..., description="Tenant identifier"),
    tag_repo: ClientTagRepository = Depends(get_client_tag_repository),
):
    """Check if a client tag name is available within a tenant."""
    tag = await tag_repo.get_by_name(name, TenantId(tenant_id))
    return {"available": tag is None, "name": name, "tenant_id": tenant_id}
