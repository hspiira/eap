"""Contact API Routes - FastAPI routes for Contact operations."""

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import TokenData, get_current_user

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
from app.domain.repositories.contact_repository import ContactRepository
from app.domain.value_objects.core import ContactId, TenantId
from app.shared.decorators import transactional, readonly
from app.shared.utils.generators import generate_cuid

router = APIRouter(prefix="/contacts", tags=["contacts"])


def _to_contact_response(contact: ContactEntity) -> ContactResponse:
    """Map ContactEntity to API response using public properties."""
    return ContactResponse(
        id=contact.id.value,
        tenant_id=contact.tenant_id.value,
        client_id=contact.client_id,
        name=contact.name,
        title=contact.title,
        email=contact.email.value if contact.email else None,
        phone=contact.phone,
        department=contact.department,
        is_primary=contact.is_primary,
        notes=contact.notes,
        is_active=contact.is_active(),
        created_at=contact.created_at.isoformat(),
        updated_at=contact.updated_at.isoformat(),
    )


@router.post(
    "/",
    response_model=ContactResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new contact",
)
@transactional()
async def create_contact(
    data: ContactCreate,
    tenant_id: str = Query(..., description="Tenant identifier"),
    current_user: TokenData = Depends(get_current_user),
    contact_repo: ContactRepository = Depends(get_contact_repository),
    db: AsyncSession = Depends(get_db),
):
    """Create a new contact."""
    if current_user.tenant_id != tenant_id:
        raise HTTPException(status_code=403, detail="Access denied to this tenant")
    contact = await CreateContactUseCase(contact_repo).execute(
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
    return _to_contact_response(contact)


@router.patch(
    "/{contact_id}",
    response_model=ContactResponse,
    summary="Update a contact",
)
@transactional()
async def update_contact(
    contact_id: str,
    data: ContactUpdate,
    contact_repo: ContactRepository = Depends(get_contact_repository),
    db: AsyncSession = Depends(get_db),
):
    """Update a contact."""
    contact = await UpdateContactUseCase(contact_repo).execute(
        ContactId(contact_id),
        name=data.name,
        title=data.title,
        email=data.email,
        phone=data.phone,
        department=data.department,
        is_primary=data.is_primary,
        notes=data.notes,
    )
    return _to_contact_response(contact)


@router.post(
    "/{contact_id}/activate",
    response_model=ContactResponse,
    summary="Activate a contact",
)
@transactional()
async def activate_contact(
    contact_id: str,
    contact_repo: ContactRepository = Depends(get_contact_repository),
    db: AsyncSession = Depends(get_db),
):
    """Activate a contact."""
    contact = await ActivateContactUseCase(contact_repo).execute(ContactId(contact_id))
    return _to_contact_response(contact)


@router.post(
    "/{contact_id}/deactivate",
    response_model=ContactResponse,
    summary="Deactivate a contact",
)
@transactional()
async def deactivate_contact(
    contact_id: str,
    contact_repo: ContactRepository = Depends(get_contact_repository),
    db: AsyncSession = Depends(get_db),
):
    """Deactivate a contact."""
    contact = await DeactivateContactUseCase(contact_repo).execute(ContactId(contact_id))
    return _to_contact_response(contact)


@router.get(
    "/",
    response_model=ContactListResponse,
    summary="List contacts with filtering and pagination",
)
@readonly()
async def list_contacts(
    tenant_id: str = Query(..., description="Tenant identifier"),
    current_user: TokenData = Depends(get_current_user),
    client_id: str | None = Query(None, description="Filter by client"),
    is_active: bool | None = Query(None, description="Filter by active status"),
    is_primary: bool | None = Query(None, description="Filter by primary status"),
    search: str | None = Query(None, description="Search in contact name"),
    page: int = Query(1, ge=1, description="Page number"),
    limit: int = Query(20, ge=1, le=100, description="Items per page"),
    contact_repo: ContactRepository = Depends(get_contact_repository),
    db: AsyncSession = Depends(get_db),
):
    """List contacts with filtering, searching, and pagination."""
    if current_user.tenant_id != tenant_id:
        raise HTTPException(status_code=403, detail="Access denied to this tenant")
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

    return ContactListResponse(
        items=[_to_contact_response(contact) for contact in contacts],
        total=total,
        page=page,
        limit=limit,
        has_more=(offset + limit) < total,
    )


@router.get(
    "/client/{client_id}",
    response_model=ContactListResponse,
    summary="Get all contacts for a client",
)
@readonly()
async def get_contacts_by_client(
    client_id: str,
    tenant_id: str = Query(..., description="Tenant identifier"),
    current_user: TokenData = Depends(get_current_user),
    contact_repo: ContactRepository = Depends(get_contact_repository),
    db: AsyncSession = Depends(get_db),
):
    """Get all contacts for a specific client."""
    if current_user.tenant_id != tenant_id:
        raise HTTPException(status_code=403, detail="Access denied to this tenant")
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
@readonly()
async def get_primary_contact(
    client_id: str,
    tenant_id: str = Query(..., description="Tenant identifier"),
    current_user: TokenData = Depends(get_current_user),
    contact_repo: ContactRepository = Depends(get_contact_repository),
    db: AsyncSession = Depends(get_db),
):
    """Get primary contact for a specific client."""
    if current_user.tenant_id != tenant_id:
        raise HTTPException(status_code=403, detail="Access denied to this tenant")
    contact = await contact_repo.get_primary_contact(client_id, TenantId(tenant_id))
    if not contact:
        raise ValueError("Primary contact not found")
    return _to_contact_response(contact)

@router.get(
    "/{contact_id}",
    response_model=ContactResponse,
    summary="Get contact by ID",
)
@readonly()
async def get_contact(
    contact_id: str,
    contact_repo: ContactRepository = Depends(get_contact_repository),
    db: AsyncSession = Depends(get_db),
):
    """Get contact by ID."""
    contact = await GetContactUseCase(contact_repo).execute(ContactId(contact_id))
    if not contact:
        raise ValueError("Contact not found")
    return _to_contact_response(contact)
