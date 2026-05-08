"""
Industry API Routes

FastAPI routes for Industry operations.
Refactored to use @transactional decorator to eliminate try/except boilerplate.
"""

from fastapi import APIRouter, Depends, Query, Request, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.authorization import require_same_tenant
from app.core.security import TokenData, get_current_user

from app.api.dependencies import get_audit_event_handler, get_industry_repository
from app.api.schemas.industry_schemas import (
    IndustryCreate,
    IndustryListResponse,
    IndustryResponse,
    IndustryUpdate,
)
from app.application.use_cases.industry_use_cases import (
    CreateIndustryUseCase,
    GetIndustryUseCase,
    UpdateIndustryUseCase,
)
from app.application.use_cases.transitions import (
    IndustryTransition,
    TransitionUseCase,
)
from app.core.database import get_db
from app.domain.entities.industry import IndustryEntity
from app.domain.repositories.industry_repository import IndustryRepository
from app.domain.value_objects.core import IndustryId, TenantId
from app.shared.decorators import transactional, readonly
from app.shared.utils.generators import generate_cuid
from app.shared.utils.route_audit_helper import audit_entity_operation

router = APIRouter(prefix="/industries", tags=["industries"])


def _to_industry_response(industry: IndustryEntity) -> IndustryResponse:
    """Map IndustryEntity to API response using public properties."""
    return IndustryResponse(
        id=industry.id.value,
        tenant_id=industry.tenant_id.value,
        name=industry.name,
        description=industry.description,
        code=industry.code,
        parent_industry_id=industry.parent_industry_id.value if industry.parent_industry_id else None,
        is_active=industry.is_active(),
        created_at=industry.created_at.isoformat(),
        updated_at=industry.updated_at.isoformat(),
    )


# ==================== COMMANDS (Use Cases) ====================


@router.post(
    "/",
    response_model=IndustryResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new industry",
)
@transactional()
async def create_industry(
    data: IndustryCreate,
    request: Request,
    tenant_id: str = Query(..., description="Tenant identifier"),
    current_user: TokenData = Depends(require_same_tenant),
    industry_repo: IndustryRepository = Depends(get_industry_repository),
    audit_handler=Depends(get_audit_event_handler),
    db: AsyncSession = Depends(get_db),
):
    """Create a new industry."""
    industry = await CreateIndustryUseCase(industry_repo).execute(
        industry_id=IndustryId(generate_cuid()),
        tenant_id=TenantId(tenant_id),
        name=data.name,
        description=data.description,
        code=data.code,
        parent_industry_id=IndustryId(data.parent_industry_id) if data.parent_industry_id else None,
    )
    await audit_entity_operation(
        entity=industry,
        audit_handler=audit_handler,
        tenant_id=tenant_id,
        user_id=current_user.user_id,
        request=request,
    )
    return _to_industry_response(industry)


@router.patch(
    "/{industry_id}",
    response_model=IndustryResponse,
    summary="Update an industry",
)
@transactional()
async def update_industry(
    industry_id: str,
    data: IndustryUpdate,
    request: Request,
    current_user: TokenData = Depends(get_current_user),
    industry_repo: IndustryRepository = Depends(get_industry_repository),
    audit_handler=Depends(get_audit_event_handler),
    db: AsyncSession = Depends(get_db),
):
    """Update an industry."""
    industry = await UpdateIndustryUseCase(industry_repo).execute(
        IndustryId(industry_id),
        name=data.name,
        description=data.description,
        code=data.code,
        parent_industry_id=IndustryId(data.parent_industry_id) if data.parent_industry_id else None,
    )
    await audit_entity_operation(
        entity=industry,
        audit_handler=audit_handler,
        tenant_id=industry.tenant_id,
        user_id=current_user.user_id,
        request=request,
    )
    return _to_industry_response(industry)


@router.post(
    "/{industry_id}/activate",
    response_model=IndustryResponse,
    summary="Activate an industry",
)
@transactional()
async def activate_industry(
    industry_id: str,
    request: Request,
    current_user: TokenData = Depends(get_current_user),
    industry_repo: IndustryRepository = Depends(get_industry_repository),
    audit_handler=Depends(get_audit_event_handler),
    db: AsyncSession = Depends(get_db),
):
    """Activate an industry."""
    use_case: TransitionUseCase = TransitionUseCase(industry_repo)
    use_case.entity_name = "Industry"
    industry = await use_case.execute(IndustryId(industry_id), IndustryTransition.ACTIVATE)
    await audit_entity_operation(
        entity=industry,
        audit_handler=audit_handler,
        tenant_id=industry.tenant_id,
        user_id=current_user.user_id,
        request=request,
    )
    return _to_industry_response(industry)


@router.post(
    "/{industry_id}/deactivate",
    response_model=IndustryResponse,
    summary="Deactivate an industry",
)
@transactional()
async def deactivate_industry(
    industry_id: str,
    request: Request,
    current_user: TokenData = Depends(get_current_user),
    industry_repo: IndustryRepository = Depends(get_industry_repository),
    audit_handler=Depends(get_audit_event_handler),
    db: AsyncSession = Depends(get_db),
):
    """Deactivate an industry."""
    use_case: TransitionUseCase = TransitionUseCase(industry_repo)
    use_case.entity_name = "Industry"
    industry = await use_case.execute(IndustryId(industry_id), IndustryTransition.DEACTIVATE)
    await audit_entity_operation(
        entity=industry,
        audit_handler=audit_handler,
        tenant_id=industry.tenant_id,
        user_id=current_user.user_id,
        request=request,
    )
    return _to_industry_response(industry)


# ==================== QUERIES (Direct Repository) ====================


@router.get(
    "/",
    response_model=IndustryListResponse,
    summary="List industries with filtering and pagination",
)
@readonly()
async def list_industries(
    tenant_id: str = Query(..., description="Tenant identifier"),
    current_user: TokenData = Depends(require_same_tenant),
    parent_id: str | None = Query(None, description="Filter by parent industry"),
    is_active: bool | None = Query(None, description="Filter by active status"),
    search: str | None = Query(None, description="Search in industry name"),
    page: int = Query(1, ge=1, description="Page number"),
    limit: int = Query(20, ge=1, le=500, description="Items per page"),
    industry_repo: IndustryRepository = Depends(get_industry_repository),
    db: AsyncSession = Depends(get_db),
):
    """List industries with filtering, searching, and pagination."""
    offset = (page - 1) * limit

    industries = await industry_repo.list_all(
        tenant_id=TenantId(tenant_id),
        parent_id=IndustryId(parent_id) if parent_id else None,
        is_active=is_active,
        search=search,
        limit=limit,
        offset=offset,
    )

    total = await industry_repo.count(
        tenant_id=TenantId(tenant_id),
        parent_id=IndustryId(parent_id) if parent_id else None,
        is_active=is_active,
        search=search,
    )

    return IndustryListResponse(
        items=[_to_industry_response(i) for i in industries],
        total=total,
        page=page,
        limit=limit,
        has_more=(offset + limit) < total,
    )


@router.get(
    "/{industry_id}",
    response_model=IndustryResponse,
    summary="Get industry by ID",
)
@readonly()
async def get_industry(
    industry_id: str,
    industry_repo: IndustryRepository = Depends(get_industry_repository),
    db: AsyncSession = Depends(get_db),
):
    """Get industry by ID."""
    industry = await GetIndustryUseCase(industry_repo).execute(IndustryId(industry_id))
    if not industry:
        raise ValueError("Industry not found")
    return _to_industry_response(industry)


@router.get(
    "/{industry_id}/children",
    response_model=IndustryListResponse,
    summary="Get child industries",
)
@readonly()
async def get_industry_children(
    industry_id: str,
    tenant_id: str = Query(..., description="Tenant identifier"),
    current_user: TokenData = Depends(require_same_tenant),
    industry_repo: IndustryRepository = Depends(get_industry_repository),
    db: AsyncSession = Depends(get_db),
):
    """Get all child industries for a parent industry."""
    children = await industry_repo.get_children(
        IndustryId(industry_id), TenantId(tenant_id)
    )
    return IndustryListResponse(
        items=[_to_industry_response(c) for c in children],
        total=len(children),
        page=1,
        limit=len(children),
        has_more=False,
    )


@router.get(
    "/check-name/{name}",
    summary="Check if industry name is available",
)
@readonly()
async def check_industry_name_availability(
    name: str,
    tenant_id: str = Query(..., description="Tenant identifier"),
    current_user: TokenData = Depends(require_same_tenant),
    industry_repo: IndustryRepository = Depends(get_industry_repository),
    db: AsyncSession = Depends(get_db),
):
    """Check if an industry name is available within a tenant."""
    industry = await industry_repo.get_by_name(name, TenantId(tenant_id))
    return {"available": industry is None, "name": name, "tenant_id": tenant_id}
