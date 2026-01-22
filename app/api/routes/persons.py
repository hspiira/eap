"""
Person API Routes

FastAPI routes for Person operations.
Follows hybrid approach: Commands use use cases, Queries use repositories directly.
"""

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import get_person_repository, get_user_repository
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
    GetPersonUseCase,
    GetPersonsByTypeUseCase,
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
from app.domain.exceptions import DomainError
from app.domain.repositories.person_repository import PersonRepository
from app.domain.repositories.user_repository import UserRepository
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
from app.shared.utils.http_errors import get_error_status_code

router = APIRouter(prefix="/persons", tags=["persons"])


def _to_person_response(person: PersonEntity) -> PersonResponse:
    """Map PersonEntity to API response."""
    # Map value objects to schemas
    employment_info = None
    if person._employment_info:
        employment_info = EmploymentInfoSchema(
            role=person._employment_info.role,
            start_date=person._employment_info.start_date,
            status=person._employment_info.status,
            department=person._employment_info.department,
            employee_id=person._employment_info.employee_id,
            end_date=person._employment_info.end_date,
        )

    license_info = None
    if person._license_info:
        license_info = LicenseInfoSchema(
            number=person._license_info.number,
            issuing_authority=person._license_info.issuing_authority,
            expiry_date=person._license_info.expiry_date,
        )

    staff_info = None
    if person._staff_info:
        staff_info = StaffInfoSchema(
            role=person._staff_info.role,
            client_id=person._staff_info.client_id.value,
            department=person._staff_info.department,
            can_manage_clients=person._staff_info.can_manage_clients,
            can_manage_services=person._staff_info.can_manage_services,
            can_view_reports=person._staff_info.can_view_reports,
        )

    dependent_info = None
    if person._dependent_info:
        dependent_info = DependentInfoSchema(
            primary_employee_id=person._dependent_info.primary_employee_id.value,
            relationship=person._dependent_info.relationship,
            guardian_id=person._dependent_info.guardian_id.value
            if person._dependent_info.guardian_id
            else None,
        )

    emergency_contact = None
    if person._emergency_contact:
        emergency_contact = EmergencyContactSchema(
            name=person._emergency_contact.name,
            phone=person._emergency_contact.phone,
            email=person._emergency_contact.email.value if person._emergency_contact.email else None,
        )

    return PersonResponse(
        id=person._id.value,
        tenant_id=person._tenant_id.value,
        user_id=person._user_id.value,
        person_type=person._person_type,
        is_dual_role=person._is_dual_role,
        secondary_person_type=person._secondary_person_type,
        status=person._status,
        employment_info=employment_info,
        license_info=license_info,
        staff_info=staff_info,
        dependent_info=dependent_info,
        emergency_contact=emergency_contact,
        last_service_date=person._last_service_date,
        is_eligible_for_services=person.is_eligible_for_services(),
    )


# ==================== COMMANDS (Use Cases) ====================


@router.post(
    "/{person_id}/activate",
    response_model=PersonResponse,
    summary="Activate a person",
)
async def activate_person(
    person_id: str,
    person_repo: PersonRepository = Depends(get_person_repository),
    db: AsyncSession = Depends(get_db),
):
    """
    Activate a person.

    This is a COMMAND operation, so it uses a use case for orchestration.
    """
    try:
        activate_use_case = ActivatePersonUseCase(person_repo)

        person = await activate_use_case.execute(PersonId(person_id))

        await db.commit()

        return _to_person_response(person)
    except ValueError as e:
        await db.rollback()
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e)) from e
    except DomainError as e:
        await db.rollback()
        status_code = get_error_status_code(str(e))
        raise HTTPException(status_code=status_code, detail=str(e)) from e


@router.post(
    "/{person_id}/deactivate",
    response_model=PersonResponse,
    summary="Deactivate a person",
)
async def deactivate_person(
    person_id: str,
    request: PersonDeactivateRequest,
    person_repo: PersonRepository = Depends(get_person_repository),
    db: AsyncSession = Depends(get_db),
):
    """
    Deactivate a person.

    This is a COMMAND operation, so it uses a use case for orchestration.
    """
    try:
        deactivate_use_case = DeactivatePersonUseCase(person_repo)

        person = await deactivate_use_case.execute(
            PersonId(person_id), request.reason
        )

        await db.commit()

        return _to_person_response(person)
    except ValueError as e:
        await db.rollback()
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e)) from e
    except DomainError as e:
        await db.rollback()
        status_code = get_error_status_code(str(e))
        raise HTTPException(status_code=status_code, detail=str(e)) from e


@router.post(
    "/{person_id}/terminate",
    response_model=PersonResponse,
    summary="Terminate a person",
)
async def terminate_person(
    person_id: str,
    request: PersonTerminateRequest,
    person_repo: PersonRepository = Depends(get_person_repository),
    db: AsyncSession = Depends(get_db),
):
    """
    Terminate a person.

    This is a COMMAND operation, so it uses a use case for orchestration.
    """
    try:
        terminate_use_case = TerminatePersonUseCase(person_repo)

        person = await terminate_use_case.execute(
            PersonId(person_id), request.reason
        )

        await db.commit()

        return _to_person_response(person)
    except ValueError as e:
        await db.rollback()
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e)) from e
    except DomainError as e:
        await db.rollback()
        status_code = get_error_status_code(str(e))
        raise HTTPException(status_code=status_code, detail=str(e)) from e


@router.post(
    "/{person_id}/secondary-role",
    response_model=PersonResponse,
    summary="Add secondary role to a person",
)
async def add_secondary_role(
    person_id: str,
    request: AddSecondaryRoleRequest,
    person_repo: PersonRepository = Depends(get_person_repository),
    db: AsyncSession = Depends(get_db),
):
    """
    Add a secondary role to a person.

    This is a COMMAND operation, so it uses a use case for orchestration.
    """
    try:
        # Convert schema to value object based on role
        if request.role == PersonType.CLIENT_EMPLOYEE:
            if not request.employment_info:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Employment info required for CLIENT_EMPLOYEE role",
                )
            info = EmploymentInfo(
                role=request.employment_info.role,
                start_date=request.employment_info.start_date,
                status=request.employment_info.status,
                department=request.employment_info.department,
                employee_id=request.employment_info.employee_id,
                end_date=request.employment_info.end_date,
            )
        elif request.role == PersonType.SERVICE_PROVIDER:
            if not request.license_info:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="License info required for SERVICE_PROVIDER role",
                )
            info = LicenseInfo(
                number=request.license_info.number,
                issuing_authority=request.license_info.issuing_authority,
                expiry_date=request.license_info.expiry_date,
            )
        elif request.role == PersonType.PLATFORM_STAFF:
            if not request.staff_info:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Staff info required for PLATFORM_STAFF role",
                )
            info = StaffInfo(
                role=request.staff_info.role,
                client_id=ClientId(request.staff_info.client_id),
                department=request.staff_info.department,
                can_manage_clients=request.staff_info.can_manage_clients,
                can_manage_services=request.staff_info.can_manage_services,
                can_view_reports=request.staff_info.can_view_reports,
            )
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid role: {request.role}",
            )

        add_role_use_case = AddSecondaryRoleUseCase(person_repo)

        person = await add_role_use_case.execute(
            PersonId(person_id), request.role, info
        )

        await db.commit()

        return _to_person_response(person)
    except ValueError as e:
        await db.rollback()
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e)) from e
    except DomainError as e:
        await db.rollback()
        status_code = get_error_status_code(str(e))
        raise HTTPException(status_code=status_code, detail=str(e)) from e


@router.delete(
    "/{person_id}/secondary-role",
    response_model=PersonResponse,
    summary="Remove secondary role from a person",
)
async def remove_secondary_role(
    person_id: str,
    person_repo: PersonRepository = Depends(get_person_repository),
    db: AsyncSession = Depends(get_db),
):
    """
    Remove secondary role from a person.

    This is a COMMAND operation, so it uses a use case for orchestration.
    """
    try:
        remove_role_use_case = RemoveSecondaryRoleUseCase(person_repo)

        person = await remove_role_use_case.execute(PersonId(person_id))

        await db.commit()

        return _to_person_response(person)
    except ValueError as e:
        await db.rollback()
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e)) from e
    except DomainError as e:
        await db.rollback()
        status_code = get_error_status_code(str(e))
        raise HTTPException(status_code=status_code, detail=str(e)) from e


@router.patch(
    "/{person_id}/emergency-contact",
    response_model=PersonResponse,
    summary="Update emergency contact",
)
async def update_emergency_contact(
    person_id: str,
    request: UpdateEmergencyContactRequest,
    person_repo: PersonRepository = Depends(get_person_repository),
    db: AsyncSession = Depends(get_db),
):
    """
    Update emergency contact for a person.

    This is a COMMAND operation, so it uses a use case for orchestration.
    """
    try:
        contact = EmergencyContact(
            name=request.emergency_contact.name,
            phone=request.emergency_contact.phone,
            email=Email(request.emergency_contact.email)
            if request.emergency_contact.email
            else None,
        )

        update_use_case = UpdateEmergencyContactUseCase(person_repo)

        person = await update_use_case.execute(PersonId(person_id), contact)

        await db.commit()

        return _to_person_response(person)
    except ValueError as e:
        await db.rollback()
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e)) from e
    except DomainError as e:
        await db.rollback()
        status_code = get_error_status_code(str(e))
        raise HTTPException(status_code=status_code, detail=str(e)) from e


@router.patch(
    "/{person_id}/employment-info",
    response_model=PersonResponse,
    summary="Update employment information",
)
async def update_employment_info(
    person_id: str,
    request: UpdateEmploymentInfoRequest,
    person_repo: PersonRepository = Depends(get_person_repository),
    db: AsyncSession = Depends(get_db),
):
    """
    Update employment information for a person.

    This is a COMMAND operation, so it uses a use case for orchestration.
    """
    try:
        info = EmploymentInfo(
            role=request.employment_info.role,
            start_date=request.employment_info.start_date,
            status=request.employment_info.status,
            department=request.employment_info.department,
            employee_id=request.employment_info.employee_id,
            end_date=request.employment_info.end_date,
        )

        update_use_case = UpdateEmploymentInfoUseCase(person_repo)

        person = await update_use_case.execute(PersonId(person_id), info)

        await db.commit()

        return _to_person_response(person)
    except ValueError as e:
        await db.rollback()
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e)) from e
    except DomainError as e:
        await db.rollback()
        status_code = get_error_status_code(str(e))
        raise HTTPException(status_code=status_code, detail=str(e)) from e


@router.patch(
    "/{person_id}/license-info",
    response_model=PersonResponse,
    summary="Update license information",
)
async def update_license_info(
    person_id: str,
    request: UpdateLicenseInfoRequest,
    person_repo: PersonRepository = Depends(get_person_repository),
    db: AsyncSession = Depends(get_db),
):
    """
    Update license information for a person.

    This is a COMMAND operation, so it uses a use case for orchestration.
    """
    try:
        info = LicenseInfo(
            number=request.license_info.number,
            issuing_authority=request.license_info.issuing_authority,
            expiry_date=request.license_info.expiry_date,
        )

        update_use_case = UpdateLicenseInfoUseCase(person_repo)

        person = await update_use_case.execute(PersonId(person_id), info)

        await db.commit()

        return _to_person_response(person)
    except ValueError as e:
        await db.rollback()
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e)) from e
    except DomainError as e:
        await db.rollback()
        status_code = get_error_status_code(str(e))
        raise HTTPException(status_code=status_code, detail=str(e)) from e


@router.patch(
    "/{person_id}/staff-info",
    response_model=PersonResponse,
    summary="Update staff information",
)
async def update_staff_info(
    person_id: str,
    request: UpdateStaffInfoRequest,
    person_repo: PersonRepository = Depends(get_person_repository),
    db: AsyncSession = Depends(get_db),
):
    """
    Update staff information for a person.

    This is a COMMAND operation, so it uses a use case for orchestration.
    """
    try:
        info = StaffInfo(
            role=request.staff_info.role,
            client_id=ClientId(request.staff_info.client_id),
            department=request.staff_info.department,
            can_manage_clients=request.staff_info.can_manage_clients,
            can_manage_services=request.staff_info.can_manage_services,
            can_view_reports=request.staff_info.can_view_reports,
        )

        update_use_case = UpdateStaffInfoUseCase(person_repo)

        person = await update_use_case.execute(PersonId(person_id), info)

        await db.commit()

        return _to_person_response(person)
    except ValueError as e:
        await db.rollback()
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e)) from e
    except DomainError as e:
        await db.rollback()
        status_code = get_error_status_code(str(e))
        raise HTTPException(status_code=status_code, detail=str(e)) from e


@router.post(
    "/{person_id}/archive",
    response_model=PersonResponse,
    summary="Archive a person",
)
async def archive_person(
    person_id: str,
    person_repo: PersonRepository = Depends(get_person_repository),
    db: AsyncSession = Depends(get_db),
):
    """
    Archive a person.

    This is a COMMAND operation, so it uses a use case for orchestration.
    """
    try:
        archive_use_case = ArchivePersonUseCase(person_repo)

        person = await archive_use_case.execute(PersonId(person_id))

        await db.commit()

        return _to_person_response(person)
    except ValueError as e:
        await db.rollback()
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e)) from e
    except DomainError as e:
        await db.rollback()
        status_code = get_error_status_code(str(e))
        raise HTTPException(status_code=status_code, detail=str(e)) from e


@router.post(
    "/{person_id}/restore",
    response_model=PersonResponse,
    summary="Restore a person",
)
async def restore_person(
    person_id: str,
    person_repo: PersonRepository = Depends(get_person_repository),
    db: AsyncSession = Depends(get_db),
):
    """
    Restore an archived or soft-deleted person.

    This is a COMMAND operation, so it uses a use case for orchestration.
    """
    try:
        restore_use_case = RestorePersonUseCase(person_repo)

        person = await restore_use_case.execute(PersonId(person_id))

        await db.commit()

        return _to_person_response(person)
    except ValueError as e:
        await db.rollback()
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e)) from e
    except DomainError as e:
        await db.rollback()
        status_code = get_error_status_code(str(e))
        raise HTTPException(status_code=status_code, detail=str(e)) from e


# ==================== QUERIES (Direct Repository) ====================


@router.get(
    "/",
    response_model=PersonListResponse,
    summary="List persons with filtering and pagination",
)
async def list_persons(
    tenant_id: str = Query(..., description="Tenant identifier"),
    status: BaseStatus | None = Query(None, description="Filter by person status"),
    person_type: PersonType | None = Query(
        None, description="Filter by person type"
    ),
    search: str | None = Query(None, description="Search in user email"),
    page: int = Query(1, ge=1, description="Page number"),
    limit: int = Query(20, ge=1, le=100, description="Items per page"),
    sort_by: str = Query("created_at", description="Field to sort by"),
    sort_desc: bool = Query(True, description="Sort in descending order"),
    person_repo: PersonRepository = Depends(get_person_repository),
):
    """
    List persons with filtering, searching, and pagination.

    This is a QUERY operation, so it calls the repository directly.
    """
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

    person_responses = [_to_person_response(person) for person in persons]

    return PersonListResponse(
        items=person_responses,
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
async def get_person(
    person_id: str,
    person_repo: PersonRepository = Depends(get_person_repository),
):
    """
    Get person by ID.

    This is a QUERY operation, so it calls the repository directly.
    No use case needed for simple reads.
    """
    person = await person_repo.get_by_id(PersonId(person_id))

    if not person:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Person not found"
        )

    return _to_person_response(person)


@router.get(
    "/user/{user_id}",
    response_model=PersonResponse,
    summary="Get person by user ID",
)
async def get_person_by_user_id(
    user_id: str,
    person_repo: PersonRepository = Depends(get_person_repository),
):
    """
    Get person by user ID.

    This is a QUERY operation, so it calls the repository directly.
    """
    person = await person_repo.get_by_user_id(UserId(user_id))

    if not person:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Person not found"
        )

    return _to_person_response(person)


@router.get(
    "/tenant/{tenant_id}/type/{person_type}",
    response_model=list[PersonResponse],
    summary="Get persons by type",
)
async def get_persons_by_type(
    tenant_id: str,
    person_type: PersonType,
    person_repo: PersonRepository = Depends(get_person_repository),
):
    """
    Get all persons of a specific type within a tenant.

    This is a QUERY operation, so it calls the repository directly.
    """
    persons = await person_repo.get_by_type(TenantId(tenant_id), person_type)

    return [_to_person_response(person) for person in persons]
