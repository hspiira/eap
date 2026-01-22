"""ServiceAssignment API Routes - FastAPI routes for ServiceAssignment operations."""

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import get_service_assignment_repository
from app.api.schemas.service_assignment_schemas import (
    ServiceAssignmentCreate,
    ServiceAssignmentListResponse,
    ServiceAssignmentResponse,
    ServiceAssignmentUpdate,
)
from app.application.use_cases.service_assignment_use_cases import (
    ActivateServiceAssignmentUseCase,
    CreateServiceAssignmentUseCase,
    DeactivateServiceAssignmentUseCase,
    GetServiceAssignmentUseCase,
    UpdateServiceAssignmentUseCase,
)
from app.core.database import get_db
from app.domain.enums import BaseStatus
from app.domain.entities.service_assignment import ServiceAssignmentEntity
from app.domain.exceptions import DomainError
from app.domain.repositories.service_assignment_repository import ServiceAssignmentRepository
from app.domain.value_objects.core import ContractId, ServiceAssignmentId, ServiceId, TenantId
from app.shared.utils.generators import generate_cuid
from app.shared.utils.http_errors import get_error_status_code

router = APIRouter(prefix="/service-assignments", tags=["service-assignments"])


def _to_service_assignment_response(assignment: ServiceAssignmentEntity) -> ServiceAssignmentResponse:
    """Map ServiceAssignmentEntity to API response."""
    return ServiceAssignmentResponse(
        id=assignment._id.value,
        tenant_id=assignment._tenant_id.value,
        service_id=assignment._service_id.value,
        contract_id=assignment._contract_id.value,
        status=assignment._status,
        assigned_at=assignment._assigned_at.isoformat() if assignment._assigned_at else None,
        assigned_by=assignment._assigned_by,
        notes=assignment._notes,
        is_active=assignment.is_active(),
        created_at=assignment._created_at.isoformat(),
        updated_at=assignment._updated_at.isoformat(),
    )


@router.post(
    "/",
    response_model=ServiceAssignmentResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new service assignment",
)
async def create_service_assignment(
    data: ServiceAssignmentCreate,
    tenant_id: str = Query(..., description="Tenant identifier"),
    assigned_by: str | None = Query(None, description="User ID who assigned"),
    assignment_repo: ServiceAssignmentRepository = Depends(get_service_assignment_repository),
    db: AsyncSession = Depends(get_db),
):
    """Create a new service assignment."""
    try:
        create_use_case = CreateServiceAssignmentUseCase(assignment_repo)
        assignment = await create_use_case.execute(
            assignment_id=ServiceAssignmentId(generate_cuid()),
            tenant_id=TenantId(tenant_id),
            service_id=ServiceId(data.service_id),
            contract_id=ContractId(data.contract_id),
            assigned_by=assigned_by,
            notes=data.notes,
        )
        await db.commit()
        return _to_service_assignment_response(assignment)
    except ValueError as e:
        await db.rollback()
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)) from e
    except DomainError as e:
        await db.rollback()
        status_code = get_error_status_code(str(e))
        raise HTTPException(status_code=status_code, detail=str(e)) from e


@router.patch(
    "/{assignment_id}",
    response_model=ServiceAssignmentResponse,
    summary="Update a service assignment",
)
async def update_service_assignment(
    assignment_id: str,
    data: ServiceAssignmentUpdate,
    assignment_repo: ServiceAssignmentRepository = Depends(get_service_assignment_repository),
    db: AsyncSession = Depends(get_db),
):
    """Update a service assignment."""
    try:
        update_use_case = UpdateServiceAssignmentUseCase(assignment_repo)
        assignment = await update_use_case.execute(
            ServiceAssignmentId(assignment_id), data.notes
        )
        await db.commit()
        return _to_service_assignment_response(assignment)
    except ValueError as e:
        await db.rollback()
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)) from e
    except DomainError as e:
        await db.rollback()
        status_code = get_error_status_code(str(e))
        raise HTTPException(status_code=status_code, detail=str(e)) from e


@router.post(
    "/{assignment_id}/activate",
    response_model=ServiceAssignmentResponse,
    summary="Activate a service assignment",
)
async def activate_service_assignment(
    assignment_id: str,
    assignment_repo: ServiceAssignmentRepository = Depends(get_service_assignment_repository),
    db: AsyncSession = Depends(get_db),
):
    """Activate a service assignment."""
    try:
        activate_use_case = ActivateServiceAssignmentUseCase(assignment_repo)
        assignment = await activate_use_case.execute(ServiceAssignmentId(assignment_id))
        await db.commit()
        return _to_service_assignment_response(assignment)
    except ValueError as e:
        await db.rollback()
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e)) from e
    except DomainError as e:
        await db.rollback()
        status_code = get_error_status_code(str(e))
        raise HTTPException(status_code=status_code, detail=str(e)) from e


@router.post(
    "/{assignment_id}/deactivate",
    response_model=ServiceAssignmentResponse,
    summary="Deactivate a service assignment",
)
async def deactivate_service_assignment(
    assignment_id: str,
    assignment_repo: ServiceAssignmentRepository = Depends(get_service_assignment_repository),
    db: AsyncSession = Depends(get_db),
):
    """Deactivate a service assignment."""
    try:
        deactivate_use_case = DeactivateServiceAssignmentUseCase(assignment_repo)
        assignment = await deactivate_use_case.execute(ServiceAssignmentId(assignment_id))
        await db.commit()
        return _to_service_assignment_response(assignment)
    except ValueError as e:
        await db.rollback()
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e)) from e
    except DomainError as e:
        await db.rollback()
        status_code = get_error_status_code(str(e))
        raise HTTPException(status_code=status_code, detail=str(e)) from e


@router.get(
    "/",
    response_model=ServiceAssignmentListResponse,
    summary="List service assignments with filtering and pagination",
)
async def list_service_assignments(
    tenant_id: str = Query(..., description="Tenant identifier"),
    service_id: str | None = Query(None, description="Filter by service"),
    contract_id: str | None = Query(None, description="Filter by contract"),
    status: BaseStatus | None = Query(None, description="Filter by status"),
    page: int = Query(1, ge=1, description="Page number"),
    limit: int = Query(20, ge=1, le=100, description="Items per page"),
    assignment_repo: ServiceAssignmentRepository = Depends(get_service_assignment_repository),
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

    assignment_responses = [_to_service_assignment_response(a) for a in assignments]

    return ServiceAssignmentListResponse(
        items=assignment_responses,
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
async def get_service_assignment(
    assignment_id: str,
    assignment_repo: ServiceAssignmentRepository = Depends(get_service_assignment_repository),
):
    """Get service assignment by ID."""
    get_use_case = GetServiceAssignmentUseCase(assignment_repo)
    assignment = await get_use_case.execute(ServiceAssignmentId(assignment_id))
    if not assignment:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Assignment not found")
    return _to_service_assignment_response(assignment)


@router.get(
    "/service/{service_id}",
    response_model=ServiceAssignmentListResponse,
    summary="Get all assignments for a service",
)
async def get_service_assignments_by_service(
    service_id: str,
    tenant_id: str = Query(..., description="Tenant identifier"),
    assignment_repo: ServiceAssignmentRepository = Depends(get_service_assignment_repository),
):
    """Get all assignments for a specific service."""
    assignments = await assignment_repo.get_by_service_id(ServiceId(service_id), TenantId(tenant_id))
    assignment_responses = [_to_service_assignment_response(a) for a in assignments]
    return ServiceAssignmentListResponse(
        items=assignment_responses,
        total=len(assignment_responses),
        page=1,
        limit=len(assignment_responses),
        has_more=False,
    )


@router.get(
    "/contract/{contract_id}",
    response_model=ServiceAssignmentListResponse,
    summary="Get all assignments for a contract",
)
async def get_service_assignments_by_contract(
    contract_id: str,
    tenant_id: str = Query(..., description="Tenant identifier"),
    assignment_repo: ServiceAssignmentRepository = Depends(get_service_assignment_repository),
):
    """Get all assignments for a specific contract."""
    assignments = await assignment_repo.get_by_contract_id(ContractId(contract_id), TenantId(tenant_id))
    assignment_responses = [_to_service_assignment_response(a) for a in assignments]
    return ServiceAssignmentListResponse(
        items=assignment_responses,
        total=len(assignment_responses),
        page=1,
        limit=len(assignment_responses),
        has_more=False,
    )
