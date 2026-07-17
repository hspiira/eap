"""ServiceAssignment API Routes - FastAPI routes for ServiceAssignment operations."""

from fastapi import APIRouter, Depends, Query, Request, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import get_audit_event_handler, get_service_assignment_repository
from app.api.schemas.service_assignment_schemas import (
    ServiceAssignmentCreate,
    ServiceAssignmentListResponse,
    ServiceAssignmentResponse,
    ServiceAssignmentUpdate,
)
from app.application.use_cases.service_assignment_use_cases import (
    CreateServiceAssignmentUseCase,
    GetServiceAssignmentUseCase,
    UpdateServiceAssignmentUseCase,
)
from app.application.use_cases.transitions import (
    ServiceAssignmentTransition,
    TransitionUseCase,
)
from app.core.authorization import require_same_tenant
from app.core.database import get_db
from app.core.security import TokenData, get_current_user
from app.domain.entities.service_assignment import ServiceAssignmentEntity
from app.domain.enums import BaseStatus
from app.domain.repositories.service_assignment_repository import ServiceAssignmentRepository
from app.domain.value_objects.core import ContractId, ServiceAssignmentId, ServiceId, TenantId
from app.shared.decorators import readonly, transactional
from app.shared.utils.generators import generate_cuid
from app.shared.utils.route_audit_helper import audit_entity_operation

router = APIRouter(prefix="/service-assignments", tags=["service-assignments"])


def _to_service_assignment_response(assignment: ServiceAssignmentEntity) -> ServiceAssignmentResponse:
    """Map ServiceAssignmentEntity to API response using public properties."""
    return ServiceAssignmentResponse(
        id=assignment.id.value,
        tenant_id=assignment.tenant_id.value,
        service_id=assignment.service_id.value,
        contract_id=assignment.contract_id.value,
        status=assignment.status,
        assigned_at=assignment.assigned_at.isoformat() if assignment.assigned_at else None,
        assigned_by=assignment.assigned_by,
        notes=assignment.notes,
        is_active=assignment.is_active(),
        created_at=assignment.created_at.isoformat(),
        updated_at=assignment.updated_at.isoformat(),
    )


@router.post(
    "/",
    response_model=ServiceAssignmentResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new service assignment",
)
@transactional()
async def create_service_assignment(
    data: ServiceAssignmentCreate,
    request: Request,
    tenant_id: str = Query(..., description="Tenant identifier"),
    assigned_by: str | None = Query(None, description="User ID who assigned"),
    current_user: TokenData = Depends(require_same_tenant),
    assignment_repo: ServiceAssignmentRepository = Depends(get_service_assignment_repository),
    audit_handler=Depends(get_audit_event_handler),
    db: AsyncSession = Depends(get_db),
):
    """Create a new service assignment."""
    assignment = await CreateServiceAssignmentUseCase(assignment_repo).execute(
        assignment_id=ServiceAssignmentId(generate_cuid()),
        tenant_id=TenantId(tenant_id),
        service_id=ServiceId(data.service_id),
        contract_id=ContractId(data.contract_id),
        assigned_by=assigned_by,
        notes=data.notes,
    )
    await audit_entity_operation(
        entity=assignment,
        audit_handler=audit_handler,
        tenant_id=tenant_id,
        user_id=current_user.user_id,
        request=request,
    )
    return _to_service_assignment_response(assignment)


@router.patch(
    "/{assignment_id}",
    response_model=ServiceAssignmentResponse,
    summary="Update a service assignment",
)
@transactional()
async def update_service_assignment(
    assignment_id: str,
    data: ServiceAssignmentUpdate,
    request: Request,
    current_user: TokenData = Depends(get_current_user),
    assignment_repo: ServiceAssignmentRepository = Depends(get_service_assignment_repository),
    audit_handler=Depends(get_audit_event_handler),
    db: AsyncSession = Depends(get_db),
):
    """Update a service assignment."""
    assignment = await UpdateServiceAssignmentUseCase(assignment_repo).execute(
        ServiceAssignmentId(assignment_id), data.notes
    )
    await audit_entity_operation(
        entity=assignment,
        audit_handler=audit_handler,
        tenant_id=assignment.tenant_id,
        user_id=current_user.user_id,
        request=request,
    )
    return _to_service_assignment_response(assignment)


@router.post(
    "/{assignment_id}/activate",
    response_model=ServiceAssignmentResponse,
    summary="Activate a service assignment",
)
@transactional()
async def activate_service_assignment(
    assignment_id: str,
    request: Request,
    current_user: TokenData = Depends(get_current_user),
    assignment_repo: ServiceAssignmentRepository = Depends(get_service_assignment_repository),
    audit_handler=Depends(get_audit_event_handler),
    db: AsyncSession = Depends(get_db),
):
    """Activate a service assignment."""
    use_case: TransitionUseCase = TransitionUseCase(assignment_repo)
    use_case.entity_name = "Assignment"
    assignment = await use_case.execute(
        ServiceAssignmentId(assignment_id), ServiceAssignmentTransition.ACTIVATE
    )
    await audit_entity_operation(
        entity=assignment,
        audit_handler=audit_handler,
        tenant_id=assignment.tenant_id,
        user_id=current_user.user_id,
        request=request,
    )
    return _to_service_assignment_response(assignment)


@router.post(
    "/{assignment_id}/deactivate",
    response_model=ServiceAssignmentResponse,
    summary="Deactivate a service assignment",
)
@transactional()
async def deactivate_service_assignment(
    assignment_id: str,
    request: Request,
    current_user: TokenData = Depends(get_current_user),
    assignment_repo: ServiceAssignmentRepository = Depends(get_service_assignment_repository),
    audit_handler=Depends(get_audit_event_handler),
    db: AsyncSession = Depends(get_db),
):
    """Deactivate a service assignment."""
    use_case: TransitionUseCase = TransitionUseCase(assignment_repo)
    use_case.entity_name = "Assignment"
    assignment = await use_case.execute(
        ServiceAssignmentId(assignment_id), ServiceAssignmentTransition.DEACTIVATE
    )
    await audit_entity_operation(
        entity=assignment,
        audit_handler=audit_handler,
        tenant_id=assignment.tenant_id,
        user_id=current_user.user_id,
        request=request,
    )
    return _to_service_assignment_response(assignment)


@router.get(
    "/",
    response_model=ServiceAssignmentListResponse,
    summary="List service assignments with filtering and pagination",
)
@readonly()
async def list_service_assignments(
    tenant_id: str = Query(..., description="Tenant identifier"),
    current_user: TokenData = Depends(require_same_tenant),
    service_id: str | None = Query(None, description="Filter by service"),
    contract_id: str | None = Query(None, description="Filter by contract"),
    status: BaseStatus | None = Query(None, description="Filter by status"),
    page: int = Query(1, ge=1, description="Page number"),
    limit: int = Query(20, ge=1, le=100, description="Items per page"),
    assignment_repo: ServiceAssignmentRepository = Depends(get_service_assignment_repository),
    db: AsyncSession = Depends(get_db),
):
    """List service assignments with filtering and pagination."""
    offset = (page - 1) * limit

    assignments = await assignment_repo.list_all(
        tenant_id=TenantId(tenant_id),
        service_id=ServiceId(service_id) if service_id else None,
        contract_id=ContractId(contract_id) if contract_id else None,
        status=status,
        limit=limit,
        offset=offset,
    )

    total = await assignment_repo.count(
        tenant_id=TenantId(tenant_id),
        service_id=ServiceId(service_id) if service_id else None,
        contract_id=ContractId(contract_id) if contract_id else None,
        status=status,
    )

    return ServiceAssignmentListResponse(
        items=[_to_service_assignment_response(a) for a in assignments],
        total=total,
        page=page,
        limit=limit,
        has_more=(offset + limit) < total,
    )


@router.get(
    "/{assignment_id}",
    response_model=ServiceAssignmentResponse,
    summary="Get service assignment by ID",
)
@readonly()
async def get_service_assignment(
    assignment_id: str,
    assignment_repo: ServiceAssignmentRepository = Depends(get_service_assignment_repository),
    db: AsyncSession = Depends(get_db),
):
    """Get service assignment by ID."""
    assignment = await GetServiceAssignmentUseCase(assignment_repo).execute(
        ServiceAssignmentId(assignment_id)
    )
    if not assignment:
        raise ValueError("Assignment not found")
    return _to_service_assignment_response(assignment)


@router.get(
    "/service/{service_id}",
    response_model=ServiceAssignmentListResponse,
    summary="Get all assignments for a service",
)
@readonly()
async def get_service_assignments_by_service(
    service_id: str,
    tenant_id: str = Query(..., description="Tenant identifier"),
    current_user: TokenData = Depends(require_same_tenant),
    assignment_repo: ServiceAssignmentRepository = Depends(get_service_assignment_repository),
    db: AsyncSession = Depends(get_db),
):
    """Get all assignments for a specific service."""
    assignments = await assignment_repo.get_by_service_id(
        ServiceId(service_id), TenantId(tenant_id)
    )
    return ServiceAssignmentListResponse(
        items=[_to_service_assignment_response(a) for a in assignments],
        total=len(assignments),
        page=1,
        limit=len(assignments),
        has_more=False,
    )


@router.get(
    "/contract/{contract_id}",
    response_model=ServiceAssignmentListResponse,
    summary="Get all assignments for a contract",
)
@readonly()
async def get_service_assignments_by_contract(
    contract_id: str,
    tenant_id: str = Query(..., description="Tenant identifier"),
    current_user: TokenData = Depends(require_same_tenant),
    assignment_repo: ServiceAssignmentRepository = Depends(get_service_assignment_repository),
    db: AsyncSession = Depends(get_db),
):
    """Get all assignments for a specific contract."""
    assignments = await assignment_repo.get_by_contract_id(
        ContractId(contract_id), TenantId(tenant_id)
    )
    return ServiceAssignmentListResponse(
        items=[_to_service_assignment_response(a) for a in assignments],
        total=len(assignments),
        page=1,
        limit=len(assignments),
        has_more=False,
    )
