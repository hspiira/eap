"""
Person API Routes

FastAPI routes for Person operations.
Refactored to use @transactional decorator to eliminate try/except boilerplate.
"""

from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import TokenData, get_current_user

from app.api.dependencies import get_audit_event_handler, get_person_repository, get_client_repository
from app.api.schemas.person_schemas import (
    AddSecondaryRoleRequest,
    DependentInfoSchema,
    EmergencyContactSchema,
    EmploymentInfoSchema,
    LicenseInfoSchema,
    PersonDeactivateRequest,
    PersonListResponse,
    PersonResponse,
    PersonTerminateRequest,
    StaffInfoSchema,
    UpdateEmergencyContactRequest,
    UpdateEmploymentInfoRequest,
    UpdateLicenseInfoRequest,
    UpdateStaffInfoRequest,
)
from app.application.use_cases.person_use_cases import (
    ActivatePersonUseCase,
    AddSecondaryRoleUseCase,
    ArchivePersonUseCase,
    DeactivatePersonUseCase,
    RemoveSecondaryRoleUseCase,
    RestorePersonUseCase,
    TerminatePersonUseCase,
    UpdateEmergencyContactUseCase,
    UpdateEmploymentInfoUseCase,
    UpdateLicenseInfoUseCase,
    UpdateStaffInfoUseCase,
)
from app.core.database import get_db
from app.domain.enums import BaseStatus, PersonType
from app.domain.entities.person import PersonEntity
from app.domain.repositories.person_repository import PersonRepository
from app.domain.repositories.client_repository import ClientRepository
from app.domain.value_objects.core import (
    ClientId,
    Email,
    EmergencyContact,
    EmploymentInfo,
    LicenseInfo,
    PersonId,
    StaffInfo,
    TenantId,
    UserId,
)
from app.shared.decorators import transactional, readonly
from app.shared.utils.route_audit_helper import audit_entity_operation

router = APIRouter(prefix="/persons", tags=["persons"])


def _to_person_response(person: PersonEntity) -> PersonResponse:
    """Map PersonEntity to API response using public properties."""
    employment_info = None
    if person.employment_info:
        employment_info = EmploymentInfoSchema(
            client_id=person.employment_info.client_id.value,
            employee_code=str(person.employment_info.employee_code),
            role=person.employment_info.role,
            start_date=person.employment_info.start_date,
            status=person.employment_info.status,
            department=person.employment_info.department,
            employee_id=person.employment_info.employee_id,
            end_date=person.employment_info.end_date,
        )

    license_info = None
    if person.license_info:
        license_info = LicenseInfoSchema(
            number=person.license_info.number,
            issuing_authority=person.license_info.issuing_authority,
            expiry_date=person.license_info.expiry_date,
        )

    staff_info = None
    if person.staff_info:
        staff_info = StaffInfoSchema(
            role=person.staff_info.role,
            client_id=person.staff_info.client_id.value,
            department=person.staff_info.department,
            can_manage_clients=person.staff_info.can_manage_clients,
            can_manage_services=person.staff_info.can_manage_services,
            can_view_reports=person.staff_info.can_view_reports,
        )

    dependent_info = None
    if person.dependent_info:
        dependent_info = DependentInfoSchema(
            primary_employee_id=person.dependent_info.primary_employee_id.value,
            relationship=person.dependent_info.relationship,
            guardian_id=person.dependent_info.guardian_id.value
            if person.dependent_info.guardian_id
            else None,
        )

    emergency_contact = None
    if person.emergency_contact:
        emergency_contact = EmergencyContactSchema(
            name=person.emergency_contact.name,
            phone=person.emergency_contact.phone,
            email=person.emergency_contact.email.value if person.emergency_contact.email else None,
        )

    return PersonResponse(
        id=person.id.value,
        tenant_id=person.tenant_id.value,
        user_id=person.user_id.value,
        person_type=person.person_type,
        is_dual_role=person.is_dual_role,
        secondary_person_type=person.secondary_person_type,
        status=person.status,
        employment_info=employment_info,
        license_info=license_info,
        staff_info=staff_info,
        dependent_info=dependent_info,
        emergency_contact=emergency_contact,
        family_id=person.family_id.value if person.family_id else None,
        last_service_date=person.last_service_date,
        is_eligible_for_services=person.is_eligible_for_services(),
    )


# ==================== COMMANDS (Use Cases) ====================


@router.post(
    "/{person_id}/activate",
    response_model=PersonResponse,
    summary="Activate a person",
)
@transactional()
async def activate_person(
    person_id: str,
    request: Request,
    current_user: TokenData = Depends(get_current_user),
    person_repo: PersonRepository = Depends(get_person_repository),
    audit_handler=Depends(get_audit_event_handler),
    db: AsyncSession = Depends(get_db),
):
    """Activate a person."""
    person = await ActivatePersonUseCase(person_repo).execute(PersonId(person_id))
    await audit_entity_operation(
        entity=person,
        audit_handler=audit_handler,
        tenant_id=person.tenant_id,
        user_id=current_user.user_id,
        request=request,
    )
    return _to_person_response(person)


@router.post(
    "/{person_id}/deactivate",
    response_model=PersonResponse,
    summary="Deactivate a person",
)
@transactional()
async def deactivate_person(
    person_id: str,
    request: Request,
    body: PersonDeactivateRequest,
    current_user: TokenData = Depends(get_current_user),
    person_repo: PersonRepository = Depends(get_person_repository),
    audit_handler=Depends(get_audit_event_handler),
    db: AsyncSession = Depends(get_db),
):
    """Deactivate a person."""
    person = await DeactivatePersonUseCase(person_repo).execute(
        PersonId(person_id), body.reason
    )
    await audit_entity_operation(
        entity=person,
        audit_handler=audit_handler,
        tenant_id=person.tenant_id,
        user_id=current_user.user_id,
        request=request,
    )
    return _to_person_response(person)


@router.post(
    "/{person_id}/terminate",
    response_model=PersonResponse,
    summary="Terminate a person",
)
@transactional()
async def terminate_person(
    person_id: str,
    request: Request,
    body: PersonTerminateRequest,
    current_user: TokenData = Depends(get_current_user),
    person_repo: PersonRepository = Depends(get_person_repository),
    audit_handler=Depends(get_audit_event_handler),
    db: AsyncSession = Depends(get_db),
):
    """Terminate a person."""
    person = await TerminatePersonUseCase(person_repo).execute(
        PersonId(person_id), body.reason
    )
    await audit_entity_operation(
        entity=person,
        audit_handler=audit_handler,
        tenant_id=person.tenant_id,
        user_id=current_user.user_id,
        request=request,
    )
    return _to_person_response(person)


@router.post(
    "/{person_id}/secondary-role",
    response_model=PersonResponse,
    summary="Add secondary role to a person",
)
@transactional()
async def add_secondary_role(
    person_id: str,
    data: AddSecondaryRoleRequest,
    request: Request,
    tenant_id: str = Query(..., description="Tenant identifier"),
    current_user: TokenData = Depends(get_current_user),
    person_repo: PersonRepository = Depends(get_person_repository),
    client_repo: ClientRepository = Depends(get_client_repository),
    audit_handler=Depends(get_audit_event_handler),
    db: AsyncSession = Depends(get_db),
):
    """Add a secondary role to a person."""
    if current_user.tenant_id != tenant_id:
        raise HTTPException(status_code=403, detail="Access denied to this tenant")
    
    if data.role == PersonType.CLIENT_EMPLOYEE:
        if not data.employment_info:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Employment info required for CLIENT_EMPLOYEE role",
            )
        from app.domain.value_objects.core import ClientEmployeeCode, EmploymentInfo
        employee_code = None
        if data.employment_info.employee_code:
            employee_code = ClientEmployeeCode.from_string(data.employment_info.employee_code)
        
        info = EmploymentInfo(
            client_id=ClientId(data.employment_info.client_id),
            employee_code=employee_code,
            role=data.employment_info.role,
            start_date=data.employment_info.start_date,
            status=data.employment_info.status,
            department=data.employment_info.department,
            employee_id=data.employment_info.employee_id,
            end_date=data.employment_info.end_date,
        )
    elif data.role == PersonType.SERVICE_PROVIDER:
        if not data.license_info:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="License info required for SERVICE_PROVIDER role",
            )
        info = LicenseInfo(
            number=data.license_info.number,
            issuing_authority=data.license_info.issuing_authority,
            expiry_date=data.license_info.expiry_date,
        )
    elif data.role == PersonType.PLATFORM_STAFF:
        if not data.staff_info:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Staff info required for PLATFORM_STAFF role",
            )
        info = StaffInfo(
            role=data.staff_info.role,
            client_id=ClientId(data.staff_info.client_id),
            department=data.staff_info.department,
            can_manage_clients=data.staff_info.can_manage_clients,
            can_manage_services=data.staff_info.can_manage_services,
            can_view_reports=data.staff_info.can_view_reports,
        )
    else:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid role: {data.role}",
        )

    person = await AddSecondaryRoleUseCase(person_repo, client_repo).execute(
        PersonId(person_id), data.role, info, TenantId(tenant_id)
    )
    await audit_entity_operation(
        entity=person,
        audit_handler=audit_handler,
        tenant_id=tenant_id,
        user_id=current_user.user_id,
        request=request,
    )
    return _to_person_response(person)


@router.delete(
    "/{person_id}/secondary-role",
    response_model=PersonResponse,
    summary="Remove secondary role from a person",
)
@transactional()
async def remove_secondary_role(
    person_id: str,
    request: Request,
    current_user: TokenData = Depends(get_current_user),
    person_repo: PersonRepository = Depends(get_person_repository),
    audit_handler=Depends(get_audit_event_handler),
    db: AsyncSession = Depends(get_db),
):
    """Remove secondary role from a person."""
    person = await RemoveSecondaryRoleUseCase(person_repo).execute(PersonId(person_id))
    await audit_entity_operation(
        entity=person,
        audit_handler=audit_handler,
        tenant_id=person.tenant_id,
        user_id=current_user.user_id,
        request=request,
    )
    return _to_person_response(person)


@router.patch(
    "/{person_id}/emergency-contact",
    response_model=PersonResponse,
    summary="Update emergency contact",
)
@transactional()
async def update_emergency_contact(
    person_id: str,
    data: UpdateEmergencyContactRequest,
    request: Request,
    current_user: TokenData = Depends(get_current_user),
    person_repo: PersonRepository = Depends(get_person_repository),
    audit_handler=Depends(get_audit_event_handler),
    db: AsyncSession = Depends(get_db),
):
    """Update emergency contact for a person."""
    contact = EmergencyContact(
        name=data.emergency_contact.name,
        phone=data.emergency_contact.phone,
        email=Email(data.emergency_contact.email)
        if data.emergency_contact.email
        else None,
    )
    person = await UpdateEmergencyContactUseCase(person_repo).execute(
        PersonId(person_id), contact
    )
    await audit_entity_operation(
        entity=person,
        audit_handler=audit_handler,
        tenant_id=person.tenant_id,
        user_id=current_user.user_id,
        request=request,
    )
    return _to_person_response(person)


@router.patch(
    "/{person_id}/employment-info",
    response_model=PersonResponse,
    summary="Update employment information",
)
@transactional()
async def update_employment_info(
    person_id: str,
    data: UpdateEmploymentInfoRequest,
    request: Request,
    current_user: TokenData = Depends(get_current_user),
    person_repo: PersonRepository = Depends(get_person_repository),
    audit_handler=Depends(get_audit_event_handler),
    db: AsyncSession = Depends(get_db),
):
    """Update employment information for a person."""
    from app.domain.value_objects.core import ClientEmployeeCode, EmploymentInfo
    employee_code = None
    if data.employment_info.employee_code:
        employee_code = ClientEmployeeCode.from_string(data.employment_info.employee_code)
    
    info = EmploymentInfo(
        client_id=ClientId(data.employment_info.client_id),
        employee_code=employee_code,
        role=data.employment_info.role,
        start_date=data.employment_info.start_date,
        status=data.employment_info.status,
        department=data.employment_info.department,
        employee_id=data.employment_info.employee_id,
        end_date=data.employment_info.end_date,
    )
    person = await UpdateEmploymentInfoUseCase(person_repo).execute(
        PersonId(person_id), info
    )
    await audit_entity_operation(
        entity=person,
        audit_handler=audit_handler,
        tenant_id=person.tenant_id,
        user_id=current_user.user_id,
        request=request,
    )
    return _to_person_response(person)


@router.patch(
    "/{person_id}/license-info",
    response_model=PersonResponse,
    summary="Update license information",
)
@transactional()
async def update_license_info(
    person_id: str,
    data: UpdateLicenseInfoRequest,
    request: Request,
    current_user: TokenData = Depends(get_current_user),
    person_repo: PersonRepository = Depends(get_person_repository),
    audit_handler=Depends(get_audit_event_handler),
    db: AsyncSession = Depends(get_db),
):
    """Update license information for a person."""
    info = LicenseInfo(
        number=data.license_info.number,
        issuing_authority=data.license_info.issuing_authority,
        expiry_date=data.license_info.expiry_date,
    )
    person = await UpdateLicenseInfoUseCase(person_repo).execute(
        PersonId(person_id), info
    )
    await audit_entity_operation(
        entity=person,
        audit_handler=audit_handler,
        tenant_id=person.tenant_id,
        user_id=current_user.user_id,
        request=request,
    )
    return _to_person_response(person)


@router.patch(
    "/{person_id}/staff-info",
    response_model=PersonResponse,
    summary="Update staff information",
)
@transactional()
async def update_staff_info(
    person_id: str,
    data: UpdateStaffInfoRequest,
    request: Request,
    current_user: TokenData = Depends(get_current_user),
    person_repo: PersonRepository = Depends(get_person_repository),
    audit_handler=Depends(get_audit_event_handler),
    db: AsyncSession = Depends(get_db),
):
    """Update staff information for a person."""
    info = StaffInfo(
        role=data.staff_info.role,
        client_id=ClientId(data.staff_info.client_id),
        department=data.staff_info.department,
        can_manage_clients=data.staff_info.can_manage_clients,
        can_manage_services=data.staff_info.can_manage_services,
        can_view_reports=data.staff_info.can_view_reports,
    )
    person = await UpdateStaffInfoUseCase(person_repo).execute(
        PersonId(person_id), info
    )
    await audit_entity_operation(
        entity=person,
        audit_handler=audit_handler,
        tenant_id=person.tenant_id,
        user_id=current_user.user_id,
        request=request,
    )
    return _to_person_response(person)


@router.post(
    "/{person_id}/archive",
    response_model=PersonResponse,
    summary="Archive a person",
)
@transactional()
async def archive_person(
    person_id: str,
    request: Request,
    current_user: TokenData = Depends(get_current_user),
    person_repo: PersonRepository = Depends(get_person_repository),
    audit_handler=Depends(get_audit_event_handler),
    db: AsyncSession = Depends(get_db),
):
    """Archive a person."""
    person = await ArchivePersonUseCase(person_repo).execute(PersonId(person_id))
    await audit_entity_operation(
        entity=person,
        audit_handler=audit_handler,
        tenant_id=person.tenant_id,
        user_id=current_user.user_id,
        request=request,
    )
    return _to_person_response(person)


@router.post(
    "/{person_id}/restore",
    response_model=PersonResponse,
    summary="Restore a person",
)
@transactional()
async def restore_person(
    person_id: str,
    request: Request,
    current_user: TokenData = Depends(get_current_user),
    person_repo: PersonRepository = Depends(get_person_repository),
    audit_handler=Depends(get_audit_event_handler),
    db: AsyncSession = Depends(get_db),
):
    """Restore an archived person to active status."""
    person = await RestorePersonUseCase(person_repo).execute(PersonId(person_id))
    await audit_entity_operation(
        entity=person,
        audit_handler=audit_handler,
        tenant_id=person.tenant_id,
        user_id=current_user.user_id,
        request=request,
    )
    return _to_person_response(person)


# ==================== QUERIES (Direct Repository) ====================


@router.get(
    "/",
    response_model=PersonListResponse,
    summary="List persons with filtering and pagination",
)
@readonly()
async def list_persons(
    tenant_id: str = Query(..., description="Tenant identifier"),
    current_user: TokenData = Depends(get_current_user),
    status: BaseStatus | None = Query(None, description="Filter by person status"),
    person_type: PersonType | None = Query(None, description="Filter by person type"),
    search: str | None = Query(None, description="Search in user email"),
    page: int = Query(1, ge=1, description="Page number"),
    limit: int = Query(20, ge=1, le=100, description="Items per page"),
    sort_by: str = Query("created_at", description="Field to sort by"),
    sort_desc: bool = Query(True, description="Sort in descending order"),
    person_repo: PersonRepository = Depends(get_person_repository),
    db: AsyncSession = Depends(get_db),
):
    """List persons with filtering, searching, and pagination."""
    if current_user.tenant_id != tenant_id:
        raise HTTPException(status_code=403, detail="Access denied to this tenant")
    offset = (page - 1) * limit

    persons = await person_repo.list_all(
        tenant_id=TenantId(tenant_id),
        status=status,
        person_type=person_type,
        search=search,
        limit=limit,
        offset=offset,
        sort_by=sort_by,
        sort_desc=sort_desc,
    )

    total = await person_repo.count(
        tenant_id=TenantId(tenant_id),
        status=status,
        person_type=person_type,
        search=search,
    )

    return PersonListResponse(
        items=[_to_person_response(person) for person in persons],
        total=total,
        page=page,
        limit=limit,
        has_more=(offset + limit) < total,
    )


@router.get(
    "/{person_id}",
    response_model=PersonResponse,
    summary="Get person by ID",
)
@readonly()
async def get_person(
    person_id: str,
    person_repo: PersonRepository = Depends(get_person_repository),
    db: AsyncSession = Depends(get_db),
):
    """Get person by ID."""
    try:
        person_id_vo = PersonId(person_id)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=f"Invalid person ID: {str(e)}")
    person = await person_repo.get_by_id(person_id_vo)
    if not person:
        raise HTTPException(status_code=404, detail="Person not found")
    return _to_person_response(person)


@router.get(
    "/user/{user_id}",
    response_model=PersonResponse,
    summary="Get person by user ID",
)
@readonly()
async def get_person_by_user_id(
    user_id: str,
    person_repo: PersonRepository = Depends(get_person_repository),
    db: AsyncSession = Depends(get_db),
):
    """Get person by user ID."""
    try:
        user_id_vo = UserId(user_id)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=f"Invalid user ID: {str(e)}")
    person = await person_repo.get_by_user_id(user_id_vo)
    if not person:
        raise HTTPException(status_code=404, detail="Person not found")
    return _to_person_response(person)


@router.get(
    "/tenant/{tenant_id}/type/{person_type}",
    response_model=list[PersonResponse],
    summary="Get persons by type",
)
@readonly()
async def get_persons_by_type(
    tenant_id: str,
    person_type: PersonType,
    current_user: TokenData = Depends(get_current_user),
    person_repo: PersonRepository = Depends(get_person_repository),
    db: AsyncSession = Depends(get_db),
):
    """Get all persons of a specific type within a tenant."""
    if current_user.tenant_id != tenant_id:
        raise HTTPException(status_code=403, detail="Access denied to this tenant")
    persons = await person_repo.get_by_type(TenantId(tenant_id), person_type)
    return [_to_person_response(person) for person in persons]
