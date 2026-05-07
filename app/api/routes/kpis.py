"""
KPI API Routes

FastAPI routes for KPI operations.
Refactored to use @transactional decorator to eliminate try/except boilerplate.
"""

from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.authorization import require_same_tenant
from app.core.security import TokenData, get_current_user

from app.api.dependencies import (
    get_audit_event_handler,
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
from app.domain.repositories.kpi_repository import (
    KPIAssignmentRepository,
    KPIRepository,
)
from app.domain.value_objects.core import KPIId, KPIAssignmentId, TenantId
from app.shared.decorators import transactional, readonly
from app.shared.utils.generators import generate_cuid
from app.shared.utils.route_audit_helper import audit_entity_operation

router = APIRouter(prefix="/kpis", tags=["kpis"])


def _to_kpi_response(kpi: KPIEntity) -> KPIResponse:
    """Map KPIEntity to API response using public properties."""
    return KPIResponse(
        id=kpi.id.value,
        tenant_id=kpi.tenant_id.value,
        name=kpi.name,
        description=kpi.description,
        category=kpi.category,
        measurement_unit=kpi.measurement_unit,
        target_value=kpi.target_value,
        threshold_min=kpi.threshold_min,
        threshold_max=kpi.threshold_max,
        formula=kpi.formula,
        is_active=kpi.is_active(),
        created_at=kpi.created_at.isoformat(),
        updated_at=kpi.updated_at.isoformat(),
    )


def _to_kpi_assignment_response(
    assignment: KPIAssignmentEntity,
) -> KPIAssignmentResponse:
    """Map KPIAssignmentEntity to API response using public properties."""
    return KPIAssignmentResponse(
        id=assignment.id.value,
        kpi_id=assignment.kpi_id.value,
        tenant_id=assignment.tenant_id.value,
        client_id=assignment.client_id,
        contract_id=assignment.contract_id,
        target_value=assignment.target_value,
        is_active=assignment.is_active(),
        created_at=assignment.created_at.isoformat(),
        updated_at=assignment.updated_at.isoformat(),
    )


# ==================== KPI COMMANDS (Use Cases) ====================


@router.post(
    "/",
    response_model=KPIResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new KPI",
)
@transactional()
async def create_kpi(
    data: KPICreate,
    request: Request,
    tenant_id: str = Query(..., description="Tenant identifier"),
    current_user: TokenData = Depends(require_same_tenant),
    kpi_repo: KPIRepository = Depends(get_kpi_repository),
    audit_handler=Depends(get_audit_event_handler),
    db: AsyncSession = Depends(get_db),
):
    """Create a new KPI."""
    kpi = await CreateKPIUseCase(kpi_repo).execute(
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
    await audit_entity_operation(
        entity=kpi,
        audit_handler=audit_handler,
        tenant_id=tenant_id,
        user_id=current_user.user_id,
        request=request,
    )
    return _to_kpi_response(kpi)


@router.patch(
    "/{kpi_id}",
    response_model=KPIResponse,
    summary="Update a KPI",
)
@transactional()
async def update_kpi(
    kpi_id: str,
    data: KPIUpdate,
    request: Request,
    current_user: TokenData = Depends(get_current_user),
    kpi_repo: KPIRepository = Depends(get_kpi_repository),
    audit_handler=Depends(get_audit_event_handler),
    db: AsyncSession = Depends(get_db),
):
    """Update a KPI."""
    kpi = await UpdateKPIUseCase(kpi_repo).execute(
        KPIId(kpi_id),
        name=data.name,
        description=data.description,
        target_value=data.target_value,
        threshold_min=data.threshold_min,
        threshold_max=data.threshold_max,
        formula=data.formula,
    )
    await audit_entity_operation(
        entity=kpi,
        audit_handler=audit_handler,
        tenant_id=kpi.tenant_id,
        user_id=current_user.user_id,
        request=request,
    )
    return _to_kpi_response(kpi)


@router.post(
    "/{kpi_id}/activate",
    response_model=KPIResponse,
    summary="Activate a KPI",
)
@transactional()
async def activate_kpi(
    kpi_id: str,
    request: Request,
    current_user: TokenData = Depends(get_current_user),
    kpi_repo: KPIRepository = Depends(get_kpi_repository),
    audit_handler=Depends(get_audit_event_handler),
    db: AsyncSession = Depends(get_db),
):
    """Activate a KPI."""
    kpi = await ActivateKPIUseCase(kpi_repo).execute(KPIId(kpi_id))
    await audit_entity_operation(
        entity=kpi,
        audit_handler=audit_handler,
        tenant_id=kpi.tenant_id,
        user_id=current_user.user_id,
        request=request,
    )
    return _to_kpi_response(kpi)


@router.post(
    "/{kpi_id}/deactivate",
    response_model=KPIResponse,
    summary="Deactivate a KPI",
)
@transactional()
async def deactivate_kpi(
    kpi_id: str,
    request: Request,
    current_user: TokenData = Depends(get_current_user),
    kpi_repo: KPIRepository = Depends(get_kpi_repository),
    audit_handler=Depends(get_audit_event_handler),
    db: AsyncSession = Depends(get_db),
):
    """Deactivate a KPI."""
    kpi = await DeactivateKPIUseCase(kpi_repo).execute(KPIId(kpi_id))
    await audit_entity_operation(
        entity=kpi,
        audit_handler=audit_handler,
        tenant_id=kpi.tenant_id,
        user_id=current_user.user_id,
        request=request,
    )
    return _to_kpi_response(kpi)


# ==================== KPI QUERIES (Direct Repository) ====================


@router.get(
    "/",
    response_model=KPIListResponse,
    summary="List KPIs with filtering and pagination",
)
@readonly()
async def list_kpis(
    tenant_id: str = Query(..., description="Tenant identifier"),
    current_user: TokenData = Depends(require_same_tenant),
    category: KPICategory | None = Query(None, description="Filter by KPI category"),
    is_active: bool | None = Query(None, description="Filter by active status"),
    search: str | None = Query(None, description="Search in KPI name or description"),
    page: int = Query(1, ge=1, description="Page number"),
    limit: int = Query(20, ge=1, le=100, description="Items per page"),
    sort_by: str = Query("created_at", description="Field to sort by"),
    sort_desc: bool = Query(True, description="Sort in descending order"),
    kpi_repo: KPIRepository = Depends(get_kpi_repository),
    db: AsyncSession = Depends(get_db),
):
    """List KPIs with filtering, searching, and pagination."""
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

    return KPIListResponse(
        items=[_to_kpi_response(kpi) for kpi in kpis],
        total=total,
        page=page,
        limit=limit,
        has_more=(offset + limit) < total,
    )


@router.get(
    "/check-name/{name}",
    summary="Check if KPI name is available",
)
@readonly()
async def check_kpi_name_availability(
    name: str,
    tenant_id: str = Query(..., description="Tenant identifier"),
    current_user: TokenData = Depends(require_same_tenant),
    kpi_repo: KPIRepository = Depends(get_kpi_repository),
    db: AsyncSession = Depends(get_db),
):
    """Check if a KPI name is available within a tenant."""
    kpi = await kpi_repo.get_by_name(name, TenantId(tenant_id))
    return {"available": kpi is None, "name": name, "tenant_id": tenant_id}

    
@router.get(
    "/{kpi_id}",
    response_model=KPIResponse,
    summary="Get KPI by ID",
)
@readonly()
async def get_kpi(
    kpi_id: str,
    kpi_repo: KPIRepository = Depends(get_kpi_repository),
    db: AsyncSession = Depends(get_db),
):
    """Get KPI by ID."""
    kpi = await GetKPIUseCase(kpi_repo).execute(KPIId(kpi_id))
    if not kpi:
        raise ValueError("KPI not found")
    return _to_kpi_response(kpi)


# ==================== KPI ASSIGNMENT COMMANDS (Use Cases) ====================


@router.post(
    "/assignments",
    response_model=KPIAssignmentResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new KPI assignment",
)
@transactional()
async def create_kpi_assignment(
    data: KPIAssignmentCreate,
    request: Request,
    tenant_id: str = Query(..., description="Tenant identifier"),
    current_user: TokenData = Depends(require_same_tenant),
    kpi_repo: KPIRepository = Depends(get_kpi_repository),
    assignment_repo: KPIAssignmentRepository = Depends(get_kpi_assignment_repository),
    audit_handler=Depends(get_audit_event_handler),
    db: AsyncSession = Depends(get_db),
):
    """Create a new KPI assignment."""
    assignment = await CreateKPIAssignmentUseCase(kpi_repo, assignment_repo).execute(
        assignment_id=KPIAssignmentId(generate_cuid()),
        kpi_id=KPIId(data.kpi_id),
        tenant_id=TenantId(tenant_id),
        client_id=data.client_id,
        contract_id=data.contract_id,
        target_value=data.target_value,
    )
    await audit_entity_operation(
        entity=assignment,
        audit_handler=audit_handler,
        tenant_id=tenant_id,
        user_id=current_user.user_id,
        request=request,
    )
    return _to_kpi_assignment_response(assignment)


@router.patch(
    "/assignments/{assignment_id}",
    response_model=KPIAssignmentResponse,
    summary="Update a KPI assignment",
)
@transactional()
async def update_kpi_assignment(
    assignment_id: str,
    data: KPIAssignmentUpdate,
    request: Request,
    current_user: TokenData = Depends(get_current_user),
    assignment_repo: KPIAssignmentRepository = Depends(get_kpi_assignment_repository),
    audit_handler=Depends(get_audit_event_handler),
    db: AsyncSession = Depends(get_db),
):
    """Update a KPI assignment."""
    assignment = await UpdateKPIAssignmentUseCase(assignment_repo).execute(
        KPIAssignmentId(assignment_id), data.target_value
    )
    await audit_entity_operation(
        entity=assignment,
        audit_handler=audit_handler,
        tenant_id=assignment.tenant_id,
        user_id=current_user.user_id,
        request=request,
    )
    return _to_kpi_assignment_response(assignment)


@router.post(
    "/assignments/{assignment_id}/activate",
    response_model=KPIAssignmentResponse,
    summary="Activate a KPI assignment",
)
@transactional()
async def activate_kpi_assignment(
    assignment_id: str,
    request: Request,
    current_user: TokenData = Depends(get_current_user),
    assignment_repo: KPIAssignmentRepository = Depends(get_kpi_assignment_repository),
    audit_handler=Depends(get_audit_event_handler),
    db: AsyncSession = Depends(get_db),
):
    """Activate a KPI assignment."""
    assignment = await ActivateKPIAssignmentUseCase(assignment_repo).execute(
        KPIAssignmentId(assignment_id)
    )
    await audit_entity_operation(
        entity=assignment,
        audit_handler=audit_handler,
        tenant_id=assignment.tenant_id,
        user_id=current_user.user_id,
        request=request,
    )
    return _to_kpi_assignment_response(assignment)


@router.post(
    "/assignments/{assignment_id}/deactivate",
    response_model=KPIAssignmentResponse,
    summary="Deactivate a KPI assignment",
)
@transactional()
async def deactivate_kpi_assignment(
    assignment_id: str,
    request: Request,
    current_user: TokenData = Depends(get_current_user),
    assignment_repo: KPIAssignmentRepository = Depends(get_kpi_assignment_repository),
    audit_handler=Depends(get_audit_event_handler),
    db: AsyncSession = Depends(get_db),
):
    """Deactivate a KPI assignment."""
    assignment = await DeactivateKPIAssignmentUseCase(assignment_repo).execute(
        KPIAssignmentId(assignment_id)
    )
    await audit_entity_operation(
        entity=assignment,
        audit_handler=audit_handler,
        tenant_id=assignment.tenant_id,
        user_id=current_user.user_id,
        request=request,
    )
    return _to_kpi_assignment_response(assignment)


# ==================== KPI ASSIGNMENT QUERIES (Direct Repository) ====================


@router.get(
    "/assignments",
    response_model=KPIAssignmentListResponse,
    summary="List KPI assignments with filtering and pagination",
)
@readonly()
async def list_kpi_assignments(
    tenant_id: str = Query(..., description="Tenant identifier"),
    current_user: TokenData = Depends(require_same_tenant),
    kpi_id: str | None = Query(None, description="Filter by KPI"),
    client_id: str | None = Query(None, description="Filter by client"),
    contract_id: str | None = Query(None, description="Filter by contract"),
    is_active: bool | None = Query(None, description="Filter by active status"),
    page: int = Query(1, ge=1, description="Page number"),
    limit: int = Query(20, ge=1, le=100, description="Items per page"),
    sort_by: str = Query("created_at", description="Field to sort by"),
    sort_desc: bool = Query(True, description="Sort in descending order"),
    assignment_repo: KPIAssignmentRepository = Depends(get_kpi_assignment_repository),
    db: AsyncSession = Depends(get_db),
):
    """List KPI assignments with filtering and pagination."""
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

    return KPIAssignmentListResponse(
        items=[_to_kpi_assignment_response(a) for a in assignments],
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
@readonly()
async def get_kpi_assignment(
    assignment_id: str,
    assignment_repo: KPIAssignmentRepository = Depends(get_kpi_assignment_repository),
    db: AsyncSession = Depends(get_db),
):
    """Get KPI assignment by ID."""
    assignment = await GetKPIAssignmentUseCase(assignment_repo).execute(
        KPIAssignmentId(assignment_id)
    )
    if not assignment:
        raise ValueError("KPI assignment not found")
    return _to_kpi_assignment_response(assignment)


@router.get(
    "/kpi/{kpi_id}/assignments",
    response_model=KPIAssignmentListResponse,
    summary="Get all assignments for a KPI",
)
@readonly()
async def get_kpi_assignments_by_kpi(
    kpi_id: str,
    tenant_id: str = Query(..., description="Tenant identifier"),
    current_user: TokenData = Depends(require_same_tenant),
    assignment_repo: KPIAssignmentRepository = Depends(get_kpi_assignment_repository),
    db: AsyncSession = Depends(get_db),
):
    """Get all assignments for a specific KPI."""
    assignments = await assignment_repo.get_by_kpi_id(
        KPIId(kpi_id), TenantId(tenant_id)
    )
    return KPIAssignmentListResponse(
        items=[_to_kpi_assignment_response(a) for a in assignments],
        total=len(assignments),
        page=1,
        limit=len(assignments),
        has_more=False,
    )


@router.get(
    "/client/{client_id}/assignments",
    response_model=KPIAssignmentListResponse,
    summary="Get all assignments for a client",
)
@readonly()
async def get_kpi_assignments_by_client(
    client_id: str,
    tenant_id: str = Query(..., description="Tenant identifier"),
    current_user: TokenData = Depends(require_same_tenant),
    assignment_repo: KPIAssignmentRepository = Depends(get_kpi_assignment_repository),
    db: AsyncSession = Depends(get_db),
):
    """Get all assignments for a specific client."""
    assignments = await assignment_repo.get_by_client_id(
        client_id, TenantId(tenant_id)
    )
    return KPIAssignmentListResponse(
        items=[_to_kpi_assignment_response(a) for a in assignments],
        total=len(assignments),
        page=1,
        limit=len(assignments),
        has_more=False,
    )


@router.get(
    "/contract/{contract_id}/assignments",
    response_model=KPIAssignmentListResponse,
    summary="Get all assignments for a contract",
)
@readonly()
async def get_kpi_assignments_by_contract(
    contract_id: str,
    tenant_id: str = Query(..., description="Tenant identifier"),
    current_user: TokenData = Depends(require_same_tenant),
    assignment_repo: KPIAssignmentRepository = Depends(get_kpi_assignment_repository),
    db: AsyncSession = Depends(get_db),
):
    """Get all assignments for a specific contract."""
    assignments = await assignment_repo.get_by_contract_id(
        contract_id, TenantId(tenant_id)
    )
    return KPIAssignmentListResponse(
        items=[_to_kpi_assignment_response(a) for a in assignments],
        total=len(assignments),
        page=1,
        limit=len(assignments),
        has_more=False,
    )
