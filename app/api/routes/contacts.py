"""Contact API Routes - FastAPI routes for Contact operations."""

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import get_contact_repository
from app.api.schemas.contact_schemas import (
    ContactCreate,
    ContactListResponse,
    ContactResponse,
    ContactUpdate,
)
from app.application.use_cases.contact_use_cases import (
    ActivateContactUseCase,
    CreateContactUseCase,
    DeactivateContactUseCase,
    GetContactUseCase,
    UpdateContactUseCase,
)
from app.core.database import get_db
from app.domain.entities.contact import ContactEntity
from app.domain.exceptions import DomainError
from app.domain.repositories.contact_repository import ContactRepository
from app.domain.value_objects.core import ContactId, TenantId
from app.shared.utils.generators import generate_cuid
from app.shared.utils.http_errors import get_error_status_code

router = APIRouter(prefix="/contacts", tags=["contacts"])


def _to_contact_response(contact: ContactEntity) -> ContactResponse:
    """Map ContactEntity to API response."""
    return ContactResponse(
        id=contact._id.value,
        tenant_id=contact._tenant_id.value,
        client_id=contact._client_id,
        name=contact._name,
        title=contact._title,
        email=contact._email.value if contact._email else None,
        phone=contact._phone,
        department=contact._department,
        is_primary=contact._is_primary,
        notes=contact._notes,
        is_active=contact.is_active(),
        created_at=contact._created_at.isoformat(),
        updated_at=contact._updated_at.isoformat(),
    )


@router.post(
    "/",
    response_model=ContactResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new contact",
)
async def create_contact(
    data: ContactCreate,
    tenant_id: str = Query(..., description="Tenant identifier"),
    contact_repo: ContactRepository = Depends(get_contact_repository),
    db: AsyncSession = Depends(get_db),
):
    """Create a new contact."""
    try:
        create_use_case = CreateContactUseCase(contact_repo)
        contact = await create_use_case.execute(
            contact_id=ContactId(generate_cuid()),
            tenant_id=TenantId(tenant_id),
            client_id=data.client_id,
            name=data.name,
            title=data.title,
            email=data.email,
            phone=data.phone,
            department=data.department,
            is_primary=data.is_primary,
            notes=data.notes,
        )
        await db.commit()
        return _to_contact_response(contact)
    except ValueError as e:
        await db.rollback()
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)) from e
    except DomainError as e:
        await db.rollback()
        status_code = get_error_status_code(str(e))
        raise HTTPException(status_code=status_code, detail=str(e)) from e


@router.patch(
    "/{contact_id}",
    response_model=ContactResponse,
    summary="Update a contact",
)
async def update_contact(
    contact_id: str,
    data: ContactUpdate,
    contact_repo: ContactRepository = Depends(get_contact_repository),
    db: AsyncSession = Depends(get_db),
):
    """Update a contact."""
    try:
        update_use_case = UpdateContactUseCase(contact_repo)
        contact = await update_use_case.execute(
            ContactId(contact_id),
            name=data.name,
            title=data.title,
            email=data.email,
            phone=data.phone,
            department=data.department,
            is_primary=data.is_primary,
            notes=data.notes,
        )
        await db.commit()
        return _to_contact_response(contact)
    except ValueError as e:
        await db.rollback()
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)) from e
    except DomainError as e:
        await db.rollback()
        status_code = get_error_status_code(str(e))
        raise HTTPException(status_code=status_code, detail=str(e)) from e


@router.post(
    "/{contact_id}/activate",
    response_model=ContactResponse,
    summary="Activate a contact",
)
async def activate_contact(
    contact_id: str,
    contact_repo: ContactRepository = Depends(get_contact_repository),
    db: AsyncSession = Depends(get_db),
):
    """Activate a contact."""
    try:
        activate_use_case = ActivateContactUseCase(contact_repo)
        contact = await activate_use_case.execute(ContactId(contact_id))
        await db.commit()
        return _to_contact_response(contact)
    except ValueError as e:
        await db.rollback()
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e)) from e
    except DomainError as e:
        await db.rollback()
        status_code = get_error_status_code(str(e))
        raise HTTPException(status_code=status_code, detail=str(e)) from e


@router.post(
    "/{contact_id}/deactivate",
    response_model=ContactResponse,
    summary="Deactivate a contact",
)
async def deactivate_contact(
    contact_id: str,
    contact_repo: ContactRepository = Depends(get_contact_repository),
    db: AsyncSession = Depends(get_db),
):
    """Deactivate a contact."""
    try:
        deactivate_use_case = DeactivateContactUseCase(contact_repo)
        contact = await deactivate_use_case.execute(ContactId(contact_id))
        await db.commit()
        return _to_contact_response(contact)
    except ValueError as e:
        await db.rollback()
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e)) from e
    except DomainError as e:
        await db.rollback()
        status_code = get_error_status_code(str(e))
        raise HTTPException(status_code=status_code, detail=str(e)) from e


@router.get(
    "/",
    response_model=ContactListResponse,
    summary="List contacts with filtering and pagination",
)
async def list_contacts(
    tenant_id: str = Query(..., description="Tenant identifier"),
    client_id: str | None = Query(None, description="Filter by client"),
    is_active: bool | None = Query(None, description="Filter by active status"),
    is_primary: bool | None = Query(None, description="Filter by primary status"),
    search: str | None = Query(None, description="Search in contact name"),
    page: int = Query(1, ge=1, description="Page number"),
    limit: int = Query(20, ge=1, le=100, description="Items per page"),
    contact_repo: ContactRepository = Depends(get_contact_repository),
):
    """List contacts with filtering, searching, and pagination."""
    offset = (page - 1) * limit

    contacts = await contact_repo.list_all(
        tenant_id=TenantId(tenant_id),
        client_id=client_id,
        is_active=is_active,
        is_primary=is_primary,
        search=search,
        limit=limit,
        offset=offset,
    )

    total = await contact_repo.count(
        tenant_id=TenantId(tenant_id),
        client_id=client_id,
        is_active=is_active,
        is_primary=is_primary,
        search=search,
    )

    contact_responses = [_to_contact_response(contact) for contact in contacts]

    return ContactListResponse(
        items=contact_responses,
        total=total,
        page=page,
        limit=limit,
        has_more=(offset + limit) < total,
    )


@router.get(
    "/{contact_id}",
    response_model=ContactResponse,
    summary="Get contact by ID",
)
async def get_contact(
    contact_id: str,
    contact_repo: ContactRepository = Depends(get_contact_repository),
):
    """Get contact by ID."""
    get_use_case = GetContactUseCase(contact_repo)
    contact = await get_use_case.execute(ContactId(contact_id))
    if not contact:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Contact not found")
    return _to_contact_response(contact)


@router.get(
    "/client/{client_id}",
    response_model=ContactListResponse,
    summary="Get all contacts for a client",
)
async def get_contacts_by_client(
    client_id: str,
    tenant_id: str = Query(..., description="Tenant identifier"),
    contact_repo: ContactRepository = Depends(get_contact_repository),
):
    """Get all contacts for a specific client."""
    contacts = await contact_repo.get_by_client_id(client_id, TenantId(tenant_id))
    contact_responses = [_to_contact_response(contact) for contact in contacts]
    return ContactListResponse(
        items=contact_responses,
        total=len(contact_responses),
        page=1,
        limit=len(contact_responses),
        has_more=False,
    )


@router.get(
    "/client/{client_id}/primary",
    response_model=ContactResponse,
    summary="Get primary contact for a client",
)
async def get_primary_contact(
    client_id: str,
    tenant_id: str = Query(..., description="Tenant identifier"),
    contact_repo: ContactRepository = Depends(get_contact_repository),
):
    """Get primary contact for a specific client."""
    contact = await contact_repo.get_primary_contact(client_id, TenantId(tenant_id))
    if not contact:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Primary contact not found")
    return _to_contact_response(contact)
