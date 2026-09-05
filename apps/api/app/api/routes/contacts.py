"""Contact API Routes - FastAPI routes for Contact operations."""

from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import (
    PageParams,
    get_audit_event_handler,
    get_contact_repository,
    pagination,
)
from app.api.schemas.contact_schemas import (
    ContactCreate,
    ContactListResponse,
    ContactResponse,
    ContactUpdate,
)
from app.application.use_cases.contact_use_cases import (
    CreateContactUseCase,
    GetContactUseCase,
    UpdateContactUseCase,
)
from app.application.use_cases.transitions import (
    ContactTransition,
    TransitionUseCase,
)
from app.core.authorization import require_same_tenant
from app.core.database import get_db
from app.core.security import TokenData, get_current_user
from app.domain.entities.contact import ContactEntity
from app.domain.repositories.contact_repository import ContactRepository
from app.domain.value_objects.core import ContactId, TenantId
from app.shared.decorators import readonly, transactional
from app.shared.utils.generators import generate_cuid
from app.shared.utils.route_audit_helper import audit_change

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
    request: Request,
    tenant_id: str = Query(..., description="Tenant identifier"),
    current_user: TokenData = Depends(require_same_tenant),
    contact_repo: ContactRepository = Depends(get_contact_repository),
    audit_handler=Depends(get_audit_event_handler),
    db: AsyncSession = Depends(get_db),
):
    """Create a new contact."""
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
    await audit_change(contact, audit_handler, current_user, request, tenant_id=tenant_id)
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
    request: Request,
    current_user: TokenData = Depends(get_current_user),
    contact_repo: ContactRepository = Depends(get_contact_repository),
    audit_handler=Depends(get_audit_event_handler),
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
    await audit_change(contact, audit_handler, current_user, request)
    return _to_contact_response(contact)


@router.post(
    "/{contact_id}/activate",
    response_model=ContactResponse,
    summary="Activate a contact",
)
@transactional()
async def activate_contact(
    contact_id: str,
    request: Request,
    current_user: TokenData = Depends(get_current_user),
    contact_repo: ContactRepository = Depends(get_contact_repository),
    audit_handler=Depends(get_audit_event_handler),
    db: AsyncSession = Depends(get_db),
):
    """Activate a contact."""
    use_case = TransitionUseCase(contact_repo, "Contact")
    contact = await use_case.execute(ContactId(contact_id), ContactTransition.ACTIVATE)
    await audit_change(contact, audit_handler, current_user, request)
    return _to_contact_response(contact)


@router.post(
    "/{contact_id}/deactivate",
    response_model=ContactResponse,
    summary="Deactivate a contact",
)
@transactional()
async def deactivate_contact(
    contact_id: str,
    request: Request,
    current_user: TokenData = Depends(get_current_user),
    contact_repo: ContactRepository = Depends(get_contact_repository),
    audit_handler=Depends(get_audit_event_handler),
    db: AsyncSession = Depends(get_db),
):
    """Deactivate a contact."""
    use_case = TransitionUseCase(contact_repo, "Contact")
    contact = await use_case.execute(ContactId(contact_id), ContactTransition.DEACTIVATE)
    await audit_change(contact, audit_handler, current_user, request)
    return _to_contact_response(contact)


@router.get(
    "/",
    response_model=ContactListResponse,
    summary="List contacts with filtering and pagination",
)
@readonly()
async def list_contacts(
    tenant_id: str = Query(..., description="Tenant identifier"),
    current_user: TokenData = Depends(require_same_tenant),
    client_id: str | None = Query(None, description="Filter by client"),
    is_active: bool | None = Query(None, description="Filter by active status"),
    is_primary: bool | None = Query(None, description="Filter by primary status"),
    search: str | None = Query(None, description="Search in contact name"),
    pg: PageParams = Depends(pagination()),
    contact_repo: ContactRepository = Depends(get_contact_repository),
    db: AsyncSession = Depends(get_db),
):
    """List contacts with filtering, searching, and pagination."""

    contacts = await contact_repo.list_all(
        tenant_id=TenantId(tenant_id),
        client_id=client_id,
        is_active=is_active,
        is_primary=is_primary,
        search=search,
        limit=pg.limit,
        offset=pg.offset,
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
        page=pg.page,
        limit=pg.limit,
        has_more=(pg.offset + pg.limit) < total,
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
    current_user: TokenData = Depends(require_same_tenant),
    contact_repo: ContactRepository = Depends(get_contact_repository),
    db: AsyncSession = Depends(get_db),
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
@readonly()
async def get_primary_contact(
    client_id: str,
    tenant_id: str = Query(..., description="Tenant identifier"),
    current_user: TokenData = Depends(require_same_tenant),
    contact_repo: ContactRepository = Depends(get_contact_repository),
    db: AsyncSession = Depends(get_db),
):
    """Get primary contact for a specific client."""
    contact = await contact_repo.get_primary_contact(client_id, TenantId(tenant_id))
    if not contact:
        raise HTTPException(status_code=404, detail="Primary contact not found")
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
