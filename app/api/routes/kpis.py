"""
KPI API Routes

FastAPI routes for KPI operations.
Follows hybrid approach: Commands use use cases, Queries use repositories directly.
"""

from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import (
    get_kpi_assignment_repository,
    get_kpi_repository,
)
from app.api.schemas.kpi_schemas import (
    KPIAssignmentCreate,
    KPIAssignmentListResponse,
    KPIAssignmentResponse,
    KPIAssignmentUpdate,
    KPICreate,
    KPIListResponse,
    KPIResponse,
    KPIUpdate,
)
from app.application.use_cases.kpi_use_cases import (
    ActivateKPIUseCase,
    ActivateKPIAssignmentUseCase,
    CreateKPIUseCase,
    CreateKPIAssignmentUseCase,
    DeactivateKPIUseCase,
    DeactivateKPIAssignmentUseCase,
    GetKPIUseCase,
    GetKPIAssignmentUseCase,
    UpdateKPIUseCase,
    UpdateKPIAssignmentUseCase,
)
from app.core.database import get_db
from app.domain.enums import KPICategory
from app.domain.entities.kpi import KPIEntity, KPIAssignmentEntity
from app.domain.exceptions import DomainError
from app.domain.repositories.kpi_repository import (
    KPIAssignmentRepository,
    KPIRepository,
)
from app.domain.value_objects.core import KPIId, KPIAssignmentId, TenantId
from app.shared.utils.generators import generate_cuid
from app.shared.utils.http_errors import get_error_status_code

router = APIRouter(prefix="/kpis", tags=["kpis"])


def _to_kpi_response(kpi: KPIEntity) -> KPIResponse:
    """Map KPIEntity to API response."""
    return KPIResponse(
        id=kpi._id.value,
        tenant_id=kpi._tenant_id.value,
        name=kpi._name,
        description=kpi._description,
        category=kpi._category,
        measurement_unit=kpi._measurement_unit,
        target_value=kpi._target_value,
        threshold_min=kpi._threshold_min,
        threshold_max=kpi._threshold_max,
        formula=kpi._formula,
        is_active=kpi.is_active(),
        created_at=kpi._created_at.isoformat(),
        updated_at=kpi._updated_at.isoformat(),
    )


def _to_kpi_assignment_response(
    assignment: KPIAssignmentEntity,
) -> KPIAssignmentResponse:
    """Map KPIAssignmentEntity to API response."""
    return KPIAssignmentResponse(
        id=assignment._id.value,
        kpi_id=assignment._kpi_id.value,
        tenant_id=assignment._tenant_id.value,
        client_id=assignment._client_id,
        contract_id=assignment._contract_id,
        target_value=assignment._target_value,
        is_active=assignment.is_active(),
        created_at=assignment._created_at.isoformat(),
        updated_at=assignment._updated_at.isoformat(),
    )


# ==================== KPI COMMANDS (Use Cases) ====================


@router.post(
    "/",
    response_model=KPIResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new KPI",
)
async def create_kpi(
    data: KPICreate,
    tenant_id: str = Query(..., description="Tenant identifier"),
    kpi_repo: KPIRepository = Depends(get_kpi_repository),
    db: AsyncSession = Depends(get_db),
):
    """
    Create a new KPI.

    This is a COMMAND operation, so it uses a use case for orchestration.
    """
    try:
        create_use_case = CreateKPIUseCase(kpi_repo)

        kpi = await create_use_case.execute(
            kpi_id=KPIId(generate_cuid()),
            tenant_id=TenantId(tenant_id),
            name=data.name,
            category=data.category,
            measurement_unit=data.measurement_unit,
            description=data.description,
            target_value=data.target_value,
            threshold_min=data.threshold_min,
            threshold_max=data.threshold_max,
            formula=data.formula,
        )

        await db.commit()

        return _to_kpi_response(kpi)
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
    "/{kpi_id}",
    response_model=KPIResponse,
    summary="Update a KPI",
)
async def update_kpi(
    kpi_id: str,
    data: KPIUpdate,
    kpi_repo: KPIRepository = Depends(get_kpi_repository),
    db: AsyncSession = Depends(get_db),
):
    """
    Update a KPI.

    This is a COMMAND operation, so it uses a use case for orchestration.
    """
    try:
        update_use_case = UpdateKPIUseCase(kpi_repo)

        kpi = await update_use_case.execute(
            KPIId(kpi_id),
            name=data.name,
            description=data.description,
            target_value=data.target_value,
            threshold_min=data.threshold_min,
            threshold_max=data.threshold_max,
            formula=data.formula,
        )

        await db.commit()

        return _to_kpi_response(kpi)
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
    "/{kpi_id}/activate",
    response_model=KPIResponse,
    summary="Activate a KPI",
)
async def activate_kpi(
    kpi_id: str,
    kpi_repo: KPIRepository = Depends(get_kpi_repository),
    db: AsyncSession = Depends(get_db),
):
    """
    Activate a KPI.

    This is a COMMAND operation, so it uses a use case for orchestration.
    """
    try:
        activate_use_case = ActivateKPIUseCase(kpi_repo)

        kpi = await activate_use_case.execute(KPIId(kpi_id))

        await db.commit()

        return _to_kpi_response(kpi)
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
    "/{kpi_id}/deactivate",
    response_model=KPIResponse,
    summary="Deactivate a KPI",
)
async def deactivate_kpi(
    kpi_id: str,
    kpi_repo: KPIRepository = Depends(get_kpi_repository),
    db: AsyncSession = Depends(get_db),
):
    """
    Deactivate a KPI.

    This is a COMMAND operation, so it uses a use case for orchestration.
    """
    try:
        deactivate_use_case = DeactivateKPIUseCase(kpi_repo)

        kpi = await deactivate_use_case.execute(KPIId(kpi_id))

        await db.commit()

        return _to_kpi_response(kpi)
    except ValueError as e:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=str(e)
        ) from e
    except DomainError as e:
        await db.rollback()
        status_code = get_error_status_code(str(e))
        raise HTTPException(status_code=status_code, detail=str(e)) from e


# ==================== KPI QUERIES (Direct Repository) ====================


@router.get(
    "/",
    response_model=KPIListResponse,
    summary="List KPIs with filtering and pagination",
)
async def list_kpis(
    tenant_id: str = Query(..., description="Tenant identifier"),
    category: KPICategory | None = Query(None, description="Filter by KPI category"),
    is_active: bool | None = Query(None, description="Filter by active status"),
    search: str | None = Query(None, description="Search in KPI name or description"),
    page: int = Query(1, ge=1, description="Page number"),
    limit: int = Query(20, ge=1, le=100, description="Items per page"),
    sort_by: str = Query("created_at", description="Field to sort by"),
    sort_desc: bool = Query(True, description="Sort in descending order"),
    kpi_repo: KPIRepository = Depends(get_kpi_repository),
):
    """
    List KPIs with filtering, searching, and pagination.

    This is a QUERY operation, so it calls the repository directly.
    """
    offset = (page - 1) * limit

    kpis = await kpi_repo.list_all(
        tenant_id=TenantId(tenant_id),
        category=category,
        is_active=is_active,
        search=search,
        limit=limit,
        offset=offset,
        sort_by=sort_by,
        sort_desc=sort_desc,
    )

    total = await kpi_repo.count(
        tenant_id=TenantId(tenant_id),
        category=category,
        is_active=is_active,
        search=search,
    )

    kpi_responses = [_to_kpi_response(kpi) for kpi in kpis]

    return KPIListResponse(
        items=kpi_responses,
        total=total,
        page=page,
        limit=limit,
        has_more=(offset + limit) < total,
    )


@router.get(
    "/{kpi_id}",
    response_model=KPIResponse,
    summary="Get KPI by ID",
)
async def get_kpi(
    kpi_id: str,
    kpi_repo: KPIRepository = Depends(get_kpi_repository),
):
    """
    Get KPI by ID.

    This is a QUERY operation, so it calls the repository directly.
    """
    get_use_case = GetKPIUseCase(kpi_repo)

    kpi = await get_use_case.execute(KPIId(kpi_id))

    if not kpi:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="KPI not found"
        )

    return _to_kpi_response(kpi)


@router.get(
    "/check-name/{name}",
    summary="Check if KPI name is available",
)
async def check_kpi_name_availability(
    name: str,
    tenant_id: str = Query(..., description="Tenant identifier"),
    kpi_repo: KPIRepository = Depends(get_kpi_repository),
):
    """
    Check if a KPI name is available within a tenant.

    This is a QUERY operation, so it calls the repository directly.
    """
    kpi = await kpi_repo.get_by_name(name, TenantId(tenant_id))

    return {"available": kpi is None, "name": name, "tenant_id": tenant_id}


# ==================== KPI ASSIGNMENT COMMANDS (Use Cases) ====================


@router.post(
    "/assignments",
    response_model=KPIAssignmentResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new KPI assignment",
)
async def create_kpi_assignment(
    data: KPIAssignmentCreate,
    tenant_id: str = Query(..., description="Tenant identifier"),
    kpi_repo: KPIRepository = Depends(get_kpi_repository),
    assignment_repo: KPIAssignmentRepository = Depends(
        get_kpi_assignment_repository
    ),
    db: AsyncSession = Depends(get_db),
):
    """
    Create a new KPI assignment.

    This is a COMMAND operation, so it uses a use case for orchestration.
    """
    try:
        create_use_case = CreateKPIAssignmentUseCase(kpi_repo, assignment_repo)

        assignment = await create_use_case.execute(
            assignment_id=KPIAssignmentId(generate_cuid()),
            kpi_id=KPIId(data.kpi_id),
            tenant_id=TenantId(tenant_id),
            client_id=data.client_id,
            contract_id=data.contract_id,
            target_value=data.target_value,
        )

        await db.commit()

        return _to_kpi_assignment_response(assignment)
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
    "/assignments/{assignment_id}",
    response_model=KPIAssignmentResponse,
    summary="Update a KPI assignment",
)
async def update_kpi_assignment(
    assignment_id: str,
    data: KPIAssignmentUpdate,
    assignment_repo: KPIAssignmentRepository = Depends(
        get_kpi_assignment_repository
    ),
    db: AsyncSession = Depends(get_db),
):
    """
    Update a KPI assignment.

    This is a COMMAND operation, so it uses a use case for orchestration.
    """
    try:
        update_use_case = UpdateKPIAssignmentUseCase(assignment_repo)

        assignment = await update_use_case.execute(
            KPIAssignmentId(assignment_id), data.target_value
        )

        await db.commit()

        return _to_kpi_assignment_response(assignment)
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
    "/assignments/{assignment_id}/activate",
    response_model=KPIAssignmentResponse,
    summary="Activate a KPI assignment",
)
async def activate_kpi_assignment(
    assignment_id: str,
    assignment_repo: KPIAssignmentRepository = Depends(
        get_kpi_assignment_repository
    ),
    db: AsyncSession = Depends(get_db),
):
    """
    Activate a KPI assignment.

    This is a COMMAND operation, so it uses a use case for orchestration.
    """
    try:
        activate_use_case = ActivateKPIAssignmentUseCase(assignment_repo)

        assignment = await activate_use_case.execute(
            KPIAssignmentId(assignment_id)
        )

        await db.commit()

        return _to_kpi_assignment_response(assignment)
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
    "/assignments/{assignment_id}/deactivate",
    response_model=KPIAssignmentResponse,
    summary="Deactivate a KPI assignment",
)
async def deactivate_kpi_assignment(
    assignment_id: str,
    assignment_repo: KPIAssignmentRepository = Depends(
        get_kpi_assignment_repository
    ),
    db: AsyncSession = Depends(get_db),
):
    """
    Deactivate a KPI assignment.

    This is a COMMAND operation, so it uses a use case for orchestration.
    """
    try:
        deactivate_use_case = DeactivateKPIAssignmentUseCase(assignment_repo)

        assignment = await deactivate_use_case.execute(
            KPIAssignmentId(assignment_id)
        )

        await db.commit()

        return _to_kpi_assignment_response(assignment)
    except ValueError as e:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=str(e)
        ) from e
    except DomainError as e:
        await db.rollback()
        status_code = get_error_status_code(str(e))
        raise HTTPException(status_code=status_code, detail=str(e)) from e


# ==================== KPI ASSIGNMENT QUERIES (Direct Repository) ====================


@router.get(
    "/assignments",
    response_model=KPIAssignmentListResponse,
    summary="List KPI assignments with filtering and pagination",
)
async def list_kpi_assignments(
    tenant_id: str = Query(..., description="Tenant identifier"),
    kpi_id: str | None = Query(None, description="Filter by KPI"),
    client_id: str | None = Query(None, description="Filter by client"),
    contract_id: str | None = Query(None, description="Filter by contract"),
    is_active: bool | None = Query(None, description="Filter by active status"),
    page: int = Query(1, ge=1, description="Page number"),
    limit: int = Query(20, ge=1, le=100, description="Items per page"),
    sort_by: str = Query("created_at", description="Field to sort by"),
    sort_desc: bool = Query(True, description="Sort in descending order"),
    assignment_repo: KPIAssignmentRepository = Depends(
        get_kpi_assignment_repository
    ),
):
    """
    List KPI assignments with filtering and pagination.

    This is a QUERY operation, so it calls the repository directly.
    """
    offset = (page - 1) * limit

    assignments = await assignment_repo.list_all(
        tenant_id=TenantId(tenant_id),
        kpi_id=KPIId(kpi_id) if kpi_id else None,
        client_id=client_id,
        contract_id=contract_id,
        is_active=is_active,
        limit=limit,
        offset=offset,
        sort_by=sort_by,
        sort_desc=sort_desc,
    )

    total = await assignment_repo.count(
        tenant_id=TenantId(tenant_id),
        kpi_id=KPIId(kpi_id) if kpi_id else None,
        client_id=client_id,
        contract_id=contract_id,
        is_active=is_active,
    )

    assignment_responses = [
        _to_kpi_assignment_response(assignment) for assignment in assignments
    ]

    return KPIAssignmentListResponse(
        items=assignment_responses,
        total=total,
        page=page,
        limit=limit,
        has_more=(offset + limit) < total,
    )


@router.get(
    "/assignments/{assignment_id}",
    response_model=KPIAssignmentResponse,
    summary="Get KPI assignment by ID",
)
async def get_kpi_assignment(
    assignment_id: str,
    assignment_repo: KPIAssignmentRepository = Depends(
        get_kpi_assignment_repository
    ),
):
    """
    Get KPI assignment by ID.

    This is a QUERY operation, so it calls the repository directly.
    """
    get_use_case = GetKPIAssignmentUseCase(assignment_repo)

    assignment = await get_use_case.execute(KPIAssignmentId(assignment_id))

    if not assignment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="KPI assignment not found",
        )

    return _to_kpi_assignment_response(assignment)


@router.get(
    "/kpi/{kpi_id}/assignments",
    response_model=KPIAssignmentListResponse,
    summary="Get all assignments for a KPI",
)
async def get_kpi_assignments_by_kpi(
    kpi_id: str,
    tenant_id: str = Query(..., description="Tenant identifier"),
    assignment_repo: KPIAssignmentRepository = Depends(
        get_kpi_assignment_repository
    ),
):
    """
    Get all assignments for a specific KPI.

    This is a QUERY operation, so it calls the repository directly.
    """
    assignments = await assignment_repo.get_by_kpi_id(
        KPIId(kpi_id), TenantId(tenant_id)
    )

    assignment_responses = [
        _to_kpi_assignment_response(assignment) for assignment in assignments
    ]

    return KPIAssignmentListResponse(
        items=assignment_responses,
        total=len(assignment_responses),
        page=1,
        limit=len(assignment_responses),
        has_more=False,
    )


@router.get(
    "/client/{client_id}/assignments",
    response_model=KPIAssignmentListResponse,
    summary="Get all assignments for a client",
)
async def get_kpi_assignments_by_client(
    client_id: str,
    tenant_id: str = Query(..., description="Tenant identifier"),
    assignment_repo: KPIAssignmentRepository = Depends(
        get_kpi_assignment_repository
    ),
):
    """
    Get all assignments for a specific client.

    This is a QUERY operation, so it calls the repository directly.
    """
    assignments = await assignment_repo.get_by_client_id(
        client_id, TenantId(tenant_id)
    )

    assignment_responses = [
        _to_kpi_assignment_response(assignment) for assignment in assignments
    ]

    return KPIAssignmentListResponse(
        items=assignment_responses,
        total=len(assignment_responses),
        page=1,
        limit=len(assignment_responses),
        has_more=False,
    )


@router.get(
    "/contract/{contract_id}/assignments",
    response_model=KPIAssignmentListResponse,
    summary="Get all assignments for a contract",
)
async def get_kpi_assignments_by_contract(
    contract_id: str,
    tenant_id: str = Query(..., description="Tenant identifier"),
    assignment_repo: KPIAssignmentRepository = Depends(
        get_kpi_assignment_repository
    ),
):
    """
    Get all assignments for a specific contract.

    This is a QUERY operation, so it calls the repository directly.
    """
    assignments = await assignment_repo.get_by_contract_id(
        contract_id, TenantId(tenant_id)
    )

    assignment_responses = [
        _to_kpi_assignment_response(assignment) for assignment in assignments
    ]

    return KPIAssignmentListResponse(
        items=assignment_responses,
        total=len(assignment_responses),
        page=1,
        limit=len(assignment_responses),
        has_more=False,
    )
