"""ClientTag API Routes - FastAPI routes for ClientTag operations."""

from fastapi import APIRouter, Depends, Query, Request, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import (
    PageParams,
    get_audit_event_handler,
    get_client_tag_repository,
    pagination,
)
from app.api.schemas.client_tag_schemas import (
    ClientTagCreate,
    ClientTagListResponse,
    ClientTagResponse,
    ClientTagUpdate,
)
from app.application.use_cases.client_tag_use_cases import (
    CreateClientTagUseCase,
    GetClientTagUseCase,
    UpdateClientTagUseCase,
)
from app.application.use_cases.transitions import (
    ClientTagTransition,
    TransitionUseCase,
)
from app.core.authorization import require_same_tenant
from app.core.database import get_db
from app.core.security import TokenData, get_current_user
from app.domain.entities.client_tag import ClientTagEntity
from app.domain.exceptions import NotFoundError
from app.domain.repositories.client_tag_repository import ClientTagRepository
from app.domain.value_objects.core import ClientTagId, TenantId
from app.shared.decorators import readonly, transactional
from app.shared.utils.generators import generate_cuid
from app.shared.utils.route_audit_helper import audit_change

router = APIRouter(prefix="/client-tags", tags=["client-tags"])


def _to_client_tag_response(tag: ClientTagEntity) -> ClientTagResponse:
    """Map ClientTagEntity to API response using public properties."""
    return ClientTagResponse(
        id=tag.id.value,
        tenant_id=tag.tenant_id.value,
        name=tag.name,
        description=tag.description,
        color=tag.color,
        is_active=tag.is_active(),
        created_at=tag.created_at.isoformat(),
        updated_at=tag.updated_at.isoformat(),
    )


@router.post(
    "/",
    response_model=ClientTagResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new client tag",
)
@transactional()
async def create_client_tag(
    data: ClientTagCreate,
    request: Request,
    tenant_id: str = Query(..., description="Tenant identifier"),
    current_user: TokenData = Depends(require_same_tenant),
    tag_repo: ClientTagRepository = Depends(get_client_tag_repository),
    audit_handler=Depends(get_audit_event_handler),
    db: AsyncSession = Depends(get_db),
):
    """Create a new client tag."""
    tag = await CreateClientTagUseCase(tag_repo).execute(
        tag_id=ClientTagId(generate_cuid()),
        tenant_id=TenantId(tenant_id),
        name=data.name,
        description=data.description,
        color=data.color,
    )
    await audit_change(tag, audit_handler, current_user, request, tenant_id=tenant_id)
    return _to_client_tag_response(tag)


@router.patch(
    "/{tag_id}",
    response_model=ClientTagResponse,
    summary="Update a client tag",
)
@transactional()
async def update_client_tag(
    tag_id: str,
    data: ClientTagUpdate,
    request: Request,
    current_user: TokenData = Depends(get_current_user),
    tag_repo: ClientTagRepository = Depends(get_client_tag_repository),
    audit_handler=Depends(get_audit_event_handler),
    db: AsyncSession = Depends(get_db),
):
    """Update a client tag."""
    tag = await UpdateClientTagUseCase(tag_repo).execute(
        ClientTagId(tag_id),
        TenantId(current_user.tenant_id),
        name=data.name,
        description=data.description,
        color=data.color,
    )
    await audit_change(tag, audit_handler, current_user, request)
    return _to_client_tag_response(tag)


@router.post(
    "/{tag_id}/activate",
    response_model=ClientTagResponse,
    summary="Activate a client tag",
)
@transactional()
async def activate_client_tag(
    tag_id: str,
    request: Request,
    current_user: TokenData = Depends(get_current_user),
    tag_repo: ClientTagRepository = Depends(get_client_tag_repository),
    audit_handler=Depends(get_audit_event_handler),
    db: AsyncSession = Depends(get_db),
):
    """Activate a client tag."""
    use_case = TransitionUseCase(tag_repo, "Tag")
    tag = await use_case.execute(ClientTagId(tag_id), ClientTagTransition.ACTIVATE)
    await audit_change(tag, audit_handler, current_user, request)
    return _to_client_tag_response(tag)


@router.post(
    "/{tag_id}/deactivate",
    response_model=ClientTagResponse,
    summary="Deactivate a client tag",
)
@transactional()
async def deactivate_client_tag(
    tag_id: str,
    request: Request,
    current_user: TokenData = Depends(get_current_user),
    tag_repo: ClientTagRepository = Depends(get_client_tag_repository),
    audit_handler=Depends(get_audit_event_handler),
    db: AsyncSession = Depends(get_db),
):
    """Deactivate a client tag."""
    use_case = TransitionUseCase(tag_repo, "Tag")
    tag = await use_case.execute(ClientTagId(tag_id), ClientTagTransition.DEACTIVATE)
    await audit_change(tag, audit_handler, current_user, request)
    return _to_client_tag_response(tag)


@router.get(
    "/",
    response_model=ClientTagListResponse,
    summary="List client tags with filtering and pagination",
)
@readonly()
async def list_client_tags(
    tenant_id: str = Query(..., description="Tenant identifier"),
    current_user: TokenData = Depends(require_same_tenant),
    is_active: bool | None = Query(None, description="Filter by active status"),
    search: str | None = Query(None, description="Search in tag name"),
    pg: PageParams = Depends(pagination()),
    tag_repo: ClientTagRepository = Depends(get_client_tag_repository),
    db: AsyncSession = Depends(get_db),
):
    """List client tags with filtering, searching, and pagination."""

    tags = await tag_repo.list_all(
        tenant_id=TenantId(tenant_id),
        is_active=is_active,
        search=search,
        limit=pg.limit,
        offset=pg.offset,
    )

    total = await tag_repo.count(
        tenant_id=TenantId(tenant_id),
        is_active=is_active,
        search=search,
    )

    return ClientTagListResponse(
        items=[_to_client_tag_response(t) for t in tags],
        total=total,
        page=pg.page,
        limit=pg.limit,
        has_more=(pg.offset + pg.limit) < total,
    )


@router.get(
    "/{tag_id}",
    response_model=ClientTagResponse,
    summary="Get client tag by ID",
)
@readonly()
async def get_client_tag(
    tag_id: str,
    tag_repo: ClientTagRepository = Depends(get_client_tag_repository),
    db: AsyncSession = Depends(get_db),
):
    """Get client tag by ID."""
    tag = await GetClientTagUseCase(tag_repo).execute(ClientTagId(tag_id))
    if not tag:
        raise NotFoundError("Tag not found")
    return _to_client_tag_response(tag)


@router.get(
    "/check-name/{name}",
    summary="Check if client tag name is available",
)
@readonly()
async def check_client_tag_name_availability(
    name: str,
    tenant_id: str = Query(..., description="Tenant identifier"),
    current_user: TokenData = Depends(require_same_tenant),
    tag_repo: ClientTagRepository = Depends(get_client_tag_repository),
    db: AsyncSession = Depends(get_db),
):
    """Check if a client tag name is available within a tenant."""
    tag = await tag_repo.get_by_name(name, TenantId(tenant_id))
    return {"available": tag is None, "name": name, "tenant_id": tenant_id}
