"""
Industry API Routes

FastAPI routes for Industry operations.
Follows hybrid approach: Commands use use cases, Queries use repositories directly.
"""

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import get_industry_repository
from app.api.schemas.industry_schemas import (
    IndustryCreate,
    IndustryListResponse,
    IndustryResponse,
    IndustryUpdate,
)
from app.application.use_cases.industry_use_cases import (
    ActivateIndustryUseCase,
    CreateIndustryUseCase,
    DeactivateIndustryUseCase,
    GetIndustryUseCase,
    UpdateIndustryUseCase,
)
from app.core.database import get_db
from app.domain.entities.industry import IndustryEntity
from app.domain.exceptions import DomainError
from app.domain.repositories.industry_repository import IndustryRepository
from app.domain.value_objects.core import IndustryId, TenantId
from app.shared.utils.generators import generate_cuid
from app.shared.utils.http_errors import get_error_status_code

router = APIRouter(prefix="/industries", tags=["industries"])


def _to_industry_response(industry: IndustryEntity) -> IndustryResponse:
    """Map IndustryEntity to API response."""
    return IndustryResponse(
        id=industry._id.value,
        tenant_id=industry._tenant_id.value,
        name=industry._name,
        description=industry._description,
        code=industry._code,
        parent_industry_id=industry._parent_industry_id.value if industry._parent_industry_id else None,
        is_active=industry.is_active(),
        created_at=industry._created_at.isoformat(),
        updated_at=industry._updated_at.isoformat(),
    )


# ==================== COMMANDS (Use Cases) ====================


@router.post(
    "/",
    response_model=IndustryResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new industry",
)
async def create_industry(
    data: IndustryCreate,
    tenant_id: str = Query(..., description="Tenant identifier"),
    industry_repo: IndustryRepository = Depends(get_industry_repository),
    db: AsyncSession = Depends(get_db),
):
    """
    Create a new industry.

    This is a COMMAND operation, so it uses a use case for orchestration.
    """
    try:
        create_use_case = CreateIndustryUseCase(industry_repo)

        industry = await create_use_case.execute(
            industry_id=IndustryId(generate_cuid()),
            tenant_id=TenantId(tenant_id),
            name=data.name,
            description=data.description,
            code=data.code,
            parent_industry_id=IndustryId(data.parent_industry_id) if data.parent_industry_id else None,
        )

        await db.commit()

        return _to_industry_response(industry)
    except ValueError as e:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)
        ) from e
    except DomainError as e:
        await db.rollback()
        status_code = get_error_status_code(str(e))
        raise HTTPException(status_code=status_code, detail=str(e)) from e


@router.patch(
    "/{industry_id}",
    response_model=IndustryResponse,
    summary="Update an industry",
)
async def update_industry(
    industry_id: str,
    data: IndustryUpdate,
    industry_repo: IndustryRepository = Depends(get_industry_repository),
    db: AsyncSession = Depends(get_db),
):
    """
    Update an industry.

    This is a COMMAND operation, so it uses a use case for orchestration.
    """
    try:
        update_use_case = UpdateIndustryUseCase(industry_repo)

        industry = await update_use_case.execute(
            IndustryId(industry_id),
            name=data.name,
            description=data.description,
            code=data.code,
            parent_industry_id=IndustryId(data.parent_industry_id) if data.parent_industry_id else None,
        )

        await db.commit()

        return _to_industry_response(industry)
    except ValueError as e:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)
        ) from e
    except DomainError as e:
        await db.rollback()
        status_code = get_error_status_code(str(e))
        raise HTTPException(status_code=status_code, detail=str(e)) from e


@router.post(
    "/{industry_id}/activate",
    response_model=IndustryResponse,
    summary="Activate an industry",
)
async def activate_industry(
    industry_id: str,
    industry_repo: IndustryRepository = Depends(get_industry_repository),
    db: AsyncSession = Depends(get_db),
):
    """
    Activate an industry.

    This is a COMMAND operation, so it uses a use case for orchestration.
    """
    try:
        activate_use_case = ActivateIndustryUseCase(industry_repo)

        industry = await activate_use_case.execute(IndustryId(industry_id))

        await db.commit()

        return _to_industry_response(industry)
    except ValueError as e:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=str(e)
        ) from e
    except DomainError as e:
        await db.rollback()
        status_code = get_error_status_code(str(e))
        raise HTTPException(status_code=status_code, detail=str(e)) from e


@router.post(
    "/{industry_id}/deactivate",
    response_model=IndustryResponse,
    summary="Deactivate an industry",
)
async def deactivate_industry(
    industry_id: str,
    industry_repo: IndustryRepository = Depends(get_industry_repository),
    db: AsyncSession = Depends(get_db),
):
    """
    Deactivate an industry.

    This is a COMMAND operation, so it uses a use case for orchestration.
    """
    try:
        deactivate_use_case = DeactivateIndustryUseCase(industry_repo)

        industry = await deactivate_use_case.execute(IndustryId(industry_id))

        await db.commit()

        return _to_industry_response(industry)
    except ValueError as e:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=str(e)
        ) from e
    except DomainError as e:
        await db.rollback()
        status_code = get_error_status_code(str(e))
        raise HTTPException(status_code=status_code, detail=str(e)) from e


# ==================== QUERIES (Direct Repository) ====================


@router.get(
    "/",
    response_model=IndustryListResponse,
    summary="List industries with filtering and pagination",
)
async def list_industries(
    tenant_id: str = Query(..., description="Tenant identifier"),
    parent_id: str | None = Query(None, description="Filter by parent industry"),
    is_active: bool | None = Query(None, description="Filter by active status"),
    search: str | None = Query(None, description="Search in industry name"),
    page: int = Query(1, ge=1, description="Page number"),
    limit: int = Query(20, ge=1, le=100, description="Items per page"),
    industry_repo: IndustryRepository = Depends(get_industry_repository),
):
    """
    List industries with filtering, searching, and pagination.

    This is a QUERY operation, so it calls the repository directly.
    """
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

    industry_responses = [_to_industry_response(industry) for industry in industries]

    return IndustryListResponse(
        items=industry_responses,
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
async def get_industry(
    industry_id: str,
    industry_repo: IndustryRepository = Depends(get_industry_repository),
):
    """
    Get industry by ID.

    This is a QUERY operation, so it calls the repository directly.
    """
    get_use_case = GetIndustryUseCase(industry_repo)

    industry = await get_use_case.execute(IndustryId(industry_id))

    if not industry:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Industry not found"
        )

    return _to_industry_response(industry)


@router.get(
    "/{industry_id}/children",
    response_model=IndustryListResponse,
    summary="Get child industries",
)
async def get_industry_children(
    industry_id: str,
    tenant_id: str = Query(..., description="Tenant identifier"),
    industry_repo: IndustryRepository = Depends(get_industry_repository),
):
    """
    Get all child industries for a parent industry.

    This is a QUERY operation, so it calls the repository directly.
    """
    children = await industry_repo.get_children(
        IndustryId(industry_id), TenantId(tenant_id)
    )

    children_responses = [_to_industry_response(child) for child in children]

    return IndustryListResponse(
        items=children_responses,
        total=len(children_responses),
        page=1,
        limit=len(children_responses),
        has_more=False,
    )


@router.get(
    "/check-name/{name}",
    summary="Check if industry name is available",
)
async def check_industry_name_availability(
    name: str,
    tenant_id: str = Query(..., description="Tenant identifier"),
    industry_repo: IndustryRepository = Depends(get_industry_repository),
):
    """
    Check if an industry name is available within a tenant.

    This is a QUERY operation, so it calls the repository directly.
    """
    industry = await industry_repo.get_by_name(name, TenantId(tenant_id))

    return {"available": industry is None, "name": name, "tenant_id": tenant_id}
