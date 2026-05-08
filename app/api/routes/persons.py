"""
Person API Routes

FastAPI routes for Person operations.
Refactored to use @transactional decorator to eliminate try/except boilerplate.
"""

from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.authorization import (
    get_person_by_user_id_for_current_tenant,
    get_person_for_current_tenant,
    require_same_tenant,
)
from app.core.security import TokenData, get_current_user

from app.api.dependencies import (
    get_audit_event_handler,
    get_client_repository,
    get_person_repository,
    get_user_repository,
)
from app.api.schemas.person_schemas import (
    AddSecondaryRoleRequest,
    DependentInfoSchema,
    EmergencyContactSchema,
    EmploymentInfoSchema,
    LicenseInfoSchema,
    PersonCreate,
    PersonDeactivateRequest,
    PersonListResponse,
    PersonResponse,
    PersonTerminateRequest,
    StaffInfoSchema,
    UpdateDependentInfoRequest,
    UpdateEmergencyContactRequest,
    UpdateEmploymentInfoRequest,
    UpdateLicenseInfoRequest,
    UpdateStaffInfoRequest,
)
from app.application.use_cases.person_use_cases import (
    ActivatePersonUseCase,
    AddSecondaryRoleUseCase,
    ArchivePersonUseCase,
    CreateClientEmployeeUseCase,
    CreateDependentUseCase,
    DeactivatePersonUseCase,
    RemoveSecondaryRoleUseCase,
    RestorePersonUseCase,
    TerminatePersonUseCase,
    UpdateDependentInfoUseCase,
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
from app.domain.repositories.user_repository import UserRepository
from app.domain.value_objects.core import (
    ClientId,
    DependentInfo,
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
from app.shared.utils.generators import generate_cuid
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
    "/",
    response_model=PersonResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new person",
)
@transactional()
async def create_person(
    data: PersonCreate,
    request: Request,
    current_user: TokenData = Depends(get_current_user),
    person_repo: PersonRepository = Depends(get_person_repository),
    client_repo: ClientRepository = Depends(get_client_repository),
    user_repo: UserRepository = Depends(get_user_repository),
    audit_handler=Depends(get_audit_event_handler),
    db: AsyncSession = Depends(get_db),
):
    """
    Create a new person (CLIENT_EMPLOYEE or DEPENDENT).

    The user identified by user_id must already exist. Persons are created after
    user registration; provide the existing user_id and type-specific payload.
    """
    if current_user.tenant_id != data.tenant_id:
        raise HTTPException(status_code=403, detail="Access denied to this tenant")

    user_id_vo = UserId(data.user_id)
    profile = await user_repo.get_by_id(user_id_vo)
    if not profile:
        raise HTTPException(status_code=404, detail="User not found")

    person_id = PersonId(generate_cuid())
    tenant_id_vo = TenantId(data.tenant_id)

    if data.person_type == PersonType.CLIENT_EMPLOYEE and data.employment_info:
        emp = data.employment_info
        family_id_vo = PersonId(data.family_id) if data.family_id else None
        try:
            person = await CreateClientEmployeeUseCase(person_repo, client_repo).execute(
                person_id=person_id,
                tenant_id=tenant_id_vo,
                user_id=user_id_vo,
                profile=profile,
                client_id=ClientId(emp.client_id),
                role=emp.role,
                start_date=emp.start_date,
                status=emp.status,
                department=emp.department,
                employee_id=emp.employee_id,
                end_date=emp.end_date,
                family_id=family_id_vo,
            )
        except ValueError as e:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    elif data.person_type == PersonType.DEPENDENT and data.dependent_info:
        dep = data.dependent_info
        dependent_info_vo = DependentInfo(
            primary_employee_id=PersonId(dep.primary_employee_id),
            relationship=dep.relationship,
            guardian_id=UserId(dep.guardian_id) if dep.guardian_id else None,
        )
        try:
            person = await CreateDependentUseCase(person_repo).execute(
                person_id=person_id,
                tenant_id=tenant_id_vo,
                user_id=user_id_vo,
                profile=profile,
                dependent_info=dependent_info_vo,
            )
        except ValueError as e:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    else:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid person_type or missing type-specific payload",
        )

    await audit_entity_operation(
        entity=person,
        audit_handler=audit_handler,
        tenant_id=data.tenant_id,
        user_id=current_user.user_id,
        request=request,
    )
    return _to_person_response(person)


@router.post(
    "/{person_id}/activate",
    response_model=PersonResponse,
    summary="Activate a person",
)
@transactional()
async def activate_person(
    request: Request,
    current_user: TokenData = Depends(get_current_user),
    person: PersonEntity = Depends(get_person_for_current_tenant),
    person_repo: PersonRepository = Depends(get_person_repository),
    audit_handler=Depends(get_audit_event_handler),
    db: AsyncSession = Depends(get_db),
):
    """Activate a person."""
    person = await ActivatePersonUseCase(person_repo).execute(person.id)
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
    request: Request,
    body: PersonDeactivateRequest,
    current_user: TokenData = Depends(get_current_user),
    person: PersonEntity = Depends(get_person_for_current_tenant),
    person_repo: PersonRepository = Depends(get_person_repository),
    audit_handler=Depends(get_audit_event_handler),
    db: AsyncSession = Depends(get_db),
):
    """Deactivate a person."""
    person = await DeactivatePersonUseCase(person_repo).execute(
        person.id, body.reason
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
    request: Request,
    body: PersonTerminateRequest,
    current_user: TokenData = Depends(get_current_user),
    person: PersonEntity = Depends(get_person_for_current_tenant),
    person_repo: PersonRepository = Depends(get_person_repository),
    audit_handler=Depends(get_audit_event_handler),
    db: AsyncSession = Depends(get_db),
):
    """Terminate a person."""
    person = await TerminatePersonUseCase(person_repo).execute(
        person.id, body.reason
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
    data: AddSecondaryRoleRequest,
    request: Request,
    tenant_id: str = Query(..., description="Tenant identifier"),
    current_user: TokenData = Depends(require_same_tenant),
    person: PersonEntity = Depends(get_person_for_current_tenant),
    person_repo: PersonRepository = Depends(get_person_repository),
    client_repo: ClientRepository = Depends(get_client_repository),
    audit_handler=Depends(get_audit_event_handler),
    db: AsyncSession = Depends(get_db),
):
    """Add a secondary role to a person."""
    
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
        person.id, data.role, info, person.tenant_id
    )
    await audit_entity_operation(
        entity=person,
        audit_handler=audit_handler,
        tenant_id=person.tenant_id.value,
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
    request: Request,
    current_user: TokenData = Depends(get_current_user),
    person: PersonEntity = Depends(get_person_for_current_tenant),
    person_repo: PersonRepository = Depends(get_person_repository),
    audit_handler=Depends(get_audit_event_handler),
    db: AsyncSession = Depends(get_db),
):
    """Remove secondary role from a person."""
    person = await RemoveSecondaryRoleUseCase(person_repo).execute(person.id)
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
    data: UpdateEmergencyContactRequest,
    request: Request,
    current_user: TokenData = Depends(get_current_user),
    person: PersonEntity = Depends(get_person_for_current_tenant),
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
        person.id, contact
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
    data: UpdateEmploymentInfoRequest,
    request: Request,
    current_user: TokenData = Depends(get_current_user),
    person: PersonEntity = Depends(get_person_for_current_tenant),
    person_repo: PersonRepository = Depends(get_person_repository),
    audit_handler=Depends(get_audit_event_handler),
    db: AsyncSession = Depends(get_db),
):
    """Update employment information for a person."""
    from app.domain.value_objects.core import ClientEmployeeCode
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
        person.id, info
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
    data: UpdateLicenseInfoRequest,
    request: Request,
    current_user: TokenData = Depends(get_current_user),
    person: PersonEntity = Depends(get_person_for_current_tenant),
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
        person.id, info
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
    data: UpdateStaffInfoRequest,
    request: Request,
    current_user: TokenData = Depends(get_current_user),
    person: PersonEntity = Depends(get_person_for_current_tenant),
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
        person.id, info
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
    "/{person_id}/dependent-info",
    response_model=PersonResponse,
    summary="Update dependent information",
)
@transactional()
async def update_dependent_info(
    data: UpdateDependentInfoRequest,
    request: Request,
    current_user: TokenData = Depends(get_current_user),
    person: PersonEntity = Depends(get_person_for_current_tenant),
    person_repo: PersonRepository = Depends(get_person_repository),
    audit_handler=Depends(get_audit_event_handler),
    db: AsyncSession = Depends(get_db),
):
    """Update dependent information for a person (must be DEPENDENT type)."""
    dep = data.dependent_info
    dependent_info_vo = DependentInfo(
        primary_employee_id=PersonId(dep.primary_employee_id),
        relationship=dep.relationship,
        guardian_id=UserId(dep.guardian_id) if dep.guardian_id else None,
    )
    person = await UpdateDependentInfoUseCase(person_repo).execute(
        person.id, dependent_info_vo
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
    request: Request,
    current_user: TokenData = Depends(get_current_user),
    person: PersonEntity = Depends(get_person_for_current_tenant),
    person_repo: PersonRepository = Depends(get_person_repository),
    audit_handler=Depends(get_audit_event_handler),
    db: AsyncSession = Depends(get_db),
):
    """Archive a person."""
    person = await ArchivePersonUseCase(person_repo).execute(person.id)
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
    request: Request,
    current_user: TokenData = Depends(get_current_user),
    person: PersonEntity = Depends(get_person_for_current_tenant),
    person_repo: PersonRepository = Depends(get_person_repository),
    audit_handler=Depends(get_audit_event_handler),
    db: AsyncSession = Depends(get_db),
):
    """Restore an archived person to active status."""
    person = await RestorePersonUseCase(person_repo).execute(person.id)
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
    current_user: TokenData = Depends(require_same_tenant),
    status: BaseStatus | None = Query(None, description="Filter by person status"),
    person_type: PersonType | None = Query(None, description="Filter by person type"),
    client_id: str | None = Query(None, description="Filter by client ID (employment_info.client_id)"),
    search: str | None = Query(None, description="Search in user email"),
    page: int = Query(1, ge=1, description="Page number"),
    limit: int = Query(20, ge=1, le=100, description="Items per page"),
    sort_by: str = Query("created_at", description="Field to sort by"),
    sort_desc: bool = Query(True, description="Sort in descending order"),
    person_repo: PersonRepository = Depends(get_person_repository),
    db: AsyncSession = Depends(get_db),
):
    """List persons with filtering, searching, and pagination."""
    offset = (page - 1) * limit
    client_id_vo = ClientId(client_id) if client_id else None

    persons = await person_repo.list_all(
        tenant_id=TenantId(tenant_id),
        status=status,
        person_type=person_type,
        client_id=client_id_vo,
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
        client_id=client_id_vo,
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
    person: PersonEntity = Depends(get_person_for_current_tenant),
    db: AsyncSession = Depends(get_db),
):
    """Get person by ID."""
    return _to_person_response(person)


@router.get(
    "/user/{user_id}",
    response_model=PersonResponse,
    summary="Get person by user ID",
)
@readonly()
async def get_person_by_user_id(
    person: PersonEntity = Depends(get_person_by_user_id_for_current_tenant),
    db: AsyncSession = Depends(get_db),
):
    """Get person by user ID."""
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
    current_user: TokenData = Depends(require_same_tenant),
    person_repo: PersonRepository = Depends(get_person_repository),
    db: AsyncSession = Depends(get_db),
):
    """Get all persons of a specific type within a tenant."""
    persons = await person_repo.get_by_type(TenantId(tenant_id), person_type)
    return [_to_person_response(person) for person in persons]
