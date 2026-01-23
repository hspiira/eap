"""
Client API Routes

FastAPI routes for Client operations.
Follows hybrid approach: Commands use use cases, Queries use repositories directly.
Refactored to use @transactional decorator to eliminate try/except boilerplate.
"""

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import get_client_repository, get_contract_repository
from app.api.schemas.client_schemas import (
    AddressSchema,
    ClientCreate,
    ClientDeactivateRequest,
    ClientListResponse,
    ClientResponse,
    ClientStatsResponse,
    ClientSuspendRequest,
    ClientTerminateRequest,
    ClientUpdate,
    ClientUpdateBillingAddress,
    ClientUpdateContactInfo,
    ContactInfoSchema,
)
from app.application.use_cases.client_use_cases import (
    ActivateClientUseCase,
    ArchiveClientUseCase,
    CreateClientUseCase,
    DeactivateClientUseCase,
    RestoreClientUseCase,
    SuspendClientUseCase,
    TerminateClientUseCase,
    UpdateClientBillingAddressUseCase,
    UpdateClientContactInfoUseCase,
    UpdateClientUseCase,
    VerifyClientUseCase,
)
from app.core.database import get_db
from app.domain.enums import BaseStatus
from app.domain.entities.client import ClientEntity
from app.domain.repositories.client_repository import ClientRepository
from app.domain.repositories.contract_repository import ContractRepository
from app.domain.value_objects.core import (
    Address,
    ClientId,
    ContactInfo,
    Email,
    IndustryId,
    TenantId,
    UserId,
)
from app.infrastructure.mappers.client_mapper import ClientMapper
from app.infrastructure.models.client_model import ClientModel
from app.shared.decorators import transactional, readonly
from app.shared.utils.generators import generate_cuid

router = APIRouter(prefix="/clients", tags=["clients"])


def _to_client_response(client: ClientEntity) -> ClientResponse:
    """Map ClientEntity to API response using public properties."""
    contact_info = ContactInfoSchema(
        phone=client.contact_info.phone,
        email=client.contact_info.email.value if client.contact_info.email else None,
        address=client.contact_info.address,
    )

    billing_address = None
    if client.billing_address:
        billing_address = AddressSchema(
            street=client.billing_address.street,
            city=client.billing_address.city,
            country=client.billing_address.country,
            postal_code=client.billing_address.postal_code,
        )

    return ClientResponse(
        id=client.id.value,
        tenant_id=client.tenant_id.value,
        name=client.name,
        status=client.status,
        is_verified=client.is_verified,
        contact_info=contact_info,
        billing_address=billing_address,
        industry_id=client.industry_id.value if client.industry_id else None,
        parent_client_id=client.parent_client_id.value if client.parent_client_id else None,
        preferred_contact_method=client.preferred_contact_method,
        is_active=client.is_active(),
    )


# ==================== COMMANDS (Use Cases) ====================


@router.post(
    "/",
    response_model=ClientResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new client",
)
@transactional()
async def create_client(
    data: ClientCreate,
    tenant_id: str = Query(..., description="Tenant identifier"),
    client_repo: ClientRepository = Depends(get_client_repository),
    db: AsyncSession = Depends(get_db),
):
    """Create a new client."""
    contact_info = ContactInfo(
        phone=data.contact_info.phone,
        email=Email(data.contact_info.email) if data.contact_info.email else None,
        address=data.contact_info.address,
    )

    billing_address = None
    if data.billing_address:
        billing_address = Address(
            street=data.billing_address.street,
            city=data.billing_address.city,
            country=data.billing_address.country,
            postal_code=data.billing_address.postal_code,
        )

    client = await CreateClientUseCase(client_repo).execute(
        client_id=ClientId(generate_cuid()),
        tenant_id=TenantId(tenant_id),
        name=data.name,
        contact_info=contact_info,
        billing_address=billing_address,
        industry_id=IndustryId(data.industry_id) if data.industry_id else None,
        parent_client_id=ClientId(data.parent_client_id) if data.parent_client_id else None,
    )

    return _to_client_response(client)


@router.post(
    "/{client_id}/verify",
    response_model=ClientResponse,
    summary="Verify a client",
)
@transactional()
async def verify_client(
    client_id: str,
    verified_by: str = Query(..., description="User ID who verified the client"),
    client_repo: ClientRepository = Depends(get_client_repository),
    db: AsyncSession = Depends(get_db),
):
    """Verify a client."""
    client = await VerifyClientUseCase(client_repo).execute(
        ClientId(client_id), UserId(verified_by)
    )
    return _to_client_response(client)


@router.post(
    "/{client_id}/activate",
    response_model=ClientResponse,
    summary="Activate a client",
)
@transactional()
async def activate_client(
    client_id: str,
    client_repo: ClientRepository = Depends(get_client_repository),
    db: AsyncSession = Depends(get_db),
):
    """Activate a client."""
    client = await ActivateClientUseCase(client_repo).execute(ClientId(client_id))
    return _to_client_response(client)


@router.post(
    "/{client_id}/deactivate",
    response_model=ClientResponse,
    summary="Deactivate a client",
)
@transactional()
async def deactivate_client(
    client_id: str,
    request: ClientDeactivateRequest,
    client_repo: ClientRepository = Depends(get_client_repository),
    db: AsyncSession = Depends(get_db),
):
    """Deactivate a client."""
    client = await DeactivateClientUseCase(client_repo).execute(
        ClientId(client_id), request.reason
    )
    return _to_client_response(client)


@router.post(
    "/{client_id}/suspend",
    response_model=ClientResponse,
    summary="Suspend a client",
)
@transactional()
async def suspend_client(
    client_id: str,
    request: ClientSuspendRequest,
    client_repo: ClientRepository = Depends(get_client_repository),
    db: AsyncSession = Depends(get_db),
):
    """Suspend a client."""
    client = await SuspendClientUseCase(client_repo).execute(
        ClientId(client_id), request.reason
    )
    return _to_client_response(client)


@router.post(
    "/{client_id}/terminate",
    response_model=ClientResponse,
    summary="Terminate a client",
)
@transactional()
async def terminate_client(
    client_id: str,
    request: ClientTerminateRequest,
    client_repo: ClientRepository = Depends(get_client_repository),
    db: AsyncSession = Depends(get_db),
):
    """Terminate a client."""
    client = await TerminateClientUseCase(client_repo).execute(
        ClientId(client_id), request.reason
    )
    return _to_client_response(client)


@router.post(
    "/{client_id}/archive",
    response_model=ClientResponse,
    summary="Archive a client",
)
@transactional()
async def archive_client(
    client_id: str,
    client_repo: ClientRepository = Depends(get_client_repository),
    db: AsyncSession = Depends(get_db),
):
    """Archive a client."""
    client = await ArchiveClientUseCase(client_repo).execute(ClientId(client_id))
    return _to_client_response(client)


@router.post(
    "/{client_id}/restore",
    response_model=ClientResponse,
    summary="Restore a client",
)
@transactional()
async def restore_client(
    client_id: str,
    client_repo: ClientRepository = Depends(get_client_repository),
    db: AsyncSession = Depends(get_db),
):
    """Restore an archived or soft-deleted client."""
    client = await RestoreClientUseCase(client_repo).execute(ClientId(client_id))
    return _to_client_response(client)


@router.patch(
    "/{client_id}",
    response_model=ClientResponse,
    summary="Update client basic information",
)
@transactional()
async def update_client(
    client_id: str,
    data: ClientUpdate,
    client_repo: ClientRepository = Depends(get_client_repository),
    db: AsyncSession = Depends(get_db),
):
    """Update client basic information."""
    client = await UpdateClientUseCase(client_repo).execute(
        ClientId(client_id),
        name=data.name,
        preferred_contact_method=data.preferred_contact_method,
    )
    return _to_client_response(client)


@router.patch(
    "/{client_id}/contact-info",
    response_model=ClientResponse,
    summary="Update client contact information",
)
@transactional()
async def update_client_contact_info(
    client_id: str,
    request: ClientUpdateContactInfo,
    client_repo: ClientRepository = Depends(get_client_repository),
    db: AsyncSession = Depends(get_db),
):
    """Update client contact information."""
    contact_info = ContactInfo(
        phone=request.contact_info.phone,
        email=Email(request.contact_info.email) if request.contact_info.email else None,
        address=request.contact_info.address,
    )

    client = await UpdateClientContactInfoUseCase(client_repo).execute(
        ClientId(client_id), contact_info
    )
    return _to_client_response(client)


@router.patch(
    "/{client_id}/billing-address",
    response_model=ClientResponse,
    summary="Update client billing address",
)
@transactional()
async def update_client_billing_address(
    client_id: str,
    request: ClientUpdateBillingAddress,
    client_repo: ClientRepository = Depends(get_client_repository),
    db: AsyncSession = Depends(get_db),
):
    """Update client billing address."""
    billing_address = None
    if request.billing_address:
        billing_address = Address(
            street=request.billing_address.street,
            city=request.billing_address.city,
            country=request.billing_address.country,
            postal_code=request.billing_address.postal_code,
        )

    client = await UpdateClientBillingAddressUseCase(client_repo).execute(
        ClientId(client_id), billing_address
    )
    return _to_client_response(client)


# ==================== QUERIES (Direct Repository) ====================


@router.get(
    "/",
    response_model=ClientListResponse,
    summary="List clients with filtering and pagination",
)
@readonly()
async def list_clients(
    tenant_id: str = Query(..., description="Tenant identifier"),
    status: BaseStatus | None = Query(None, description="Filter by client status"),
    is_verified: bool | None = Query(None, description="Filter by verification status"),
    search: str | None = Query(None, description="Search in client name"),
    page: int = Query(1, ge=1, description="Page number"),
    limit: int = Query(20, ge=1, le=100, description="Items per page"),
    sort_by: str = Query("created_at", description="Field to sort by"),
    sort_desc: bool = Query(True, description="Sort in descending order"),
    client_repo: ClientRepository = Depends(get_client_repository),
    db: AsyncSession = Depends(get_db),
):
    """List clients with filtering, searching, and pagination."""
    offset = (page - 1) * limit

    clients = await client_repo.list_all(
        tenant_id=TenantId(tenant_id),
        status=status,
        is_verified=is_verified,
        search=search,
        limit=limit,
        offset=offset,
        sort_by=sort_by,
        sort_desc=sort_desc,
    )

    total = await client_repo.count(
        tenant_id=TenantId(tenant_id),
        status=status,
        is_verified=is_verified,
        search=search,
    )

    return ClientListResponse(
        items=[_to_client_response(client) for client in clients],
        total=total,
        page=page,
        limit=limit,
        has_more=(offset + limit) < total,
    )


@router.get(
    "/{client_id}",
    response_model=ClientResponse,
    summary="Get client by ID",
)
@readonly()
async def get_client(
    client_id: str,
    client_repo: ClientRepository = Depends(get_client_repository),
    db: AsyncSession = Depends(get_db),
):
    """Get client by ID."""
    client = await client_repo.get_by_id(ClientId(client_id))
    if not client:
        raise ValueError("Client not found")
    return _to_client_response(client)


@router.get(
    "/name/{name}",
    response_model=ClientResponse,
    summary="Get client by name",
)
@readonly()
async def get_client_by_name(
    name: str,
    tenant_id: str = Query(..., description="Tenant identifier"),
    client_repo: ClientRepository = Depends(get_client_repository),
    db: AsyncSession = Depends(get_db),
):
    """Get client by name within a tenant."""
    client = await client_repo.get_by_name(TenantId(tenant_id), name)
    if not client:
        raise ValueError("Client not found")
    return _to_client_response(client)


@router.get(
    "/check-name/{name}",
    summary="Check if client name is available",
)
@readonly()
async def check_name_availability(
    name: str,
    tenant_id: str = Query(..., description="Tenant identifier"),
    client_repo: ClientRepository = Depends(get_client_repository),
    db: AsyncSession = Depends(get_db),
):
    """Check if a client name is available within a tenant."""
    client = await client_repo.get_by_name(TenantId(tenant_id), name)
    return {"available": client is None, "name": name, "tenant_id": tenant_id}


@router.get(
    "/{client_id}/stats",
    response_model=ClientStatsResponse,
    summary="Get client statistics",
)
@readonly()
async def get_client_stats(
    client_id: str,
    tenant_id: str = Query(..., description="Tenant identifier"),
    client_repo: ClientRepository = Depends(get_client_repository),
    contract_repo: ContractRepository = Depends(get_contract_repository),
    db: AsyncSession = Depends(get_db),
):
    """Get client statistics including child clients and contracts."""
    client = await client_repo.get_by_id(ClientId(client_id))
    if not client:
        raise ValueError("Client not found")

    # Count child clients
    child_clients_stmt = select(func.count(ClientModel.id)).where(
        ClientModel.tenant_id == tenant_id,
        ClientModel.parent_client_id == client_id,
        ClientModel.deleted_at.is_(None),
    )
    child_result = await db.execute(child_clients_stmt)
    child_clients_count = int(child_result.scalar() or 0)

    # Count total contracts
    contracts = await contract_repo.get_by_client_id(
        TenantId(tenant_id), ClientId(client_id)
    )
    total_contracts_count = len(contracts)

    # Count active contracts
    active_contract = await contract_repo.get_active_by_client_id(
        TenantId(tenant_id), ClientId(client_id)
    )
    active_contracts_count = 1 if active_contract else 0

    return ClientStatsResponse(
        client_id=client_id,
        child_clients_count=child_clients_count,
        total_contracts_count=total_contracts_count,
        active_contracts_count=active_contracts_count,
        is_verified=client.is_verified,
        status=client.status,
    )


@router.get(
    "/{client_id}/children",
    response_model=ClientListResponse,
    summary="Get child clients of a parent client",
)
@readonly()
async def get_child_clients(
    client_id: str,
    tenant_id: str = Query(..., description="Tenant identifier"),
    page: int = Query(1, ge=1, description="Page number"),
    limit: int = Query(20, ge=1, le=100, description="Items per page"),
    client_repo: ClientRepository = Depends(get_client_repository),
    db: AsyncSession = Depends(get_db),
):
    """Get all child clients of a parent client."""
    # Verify parent client exists
    parent = await client_repo.get_by_id(ClientId(client_id))
    if not parent:
        raise ValueError("Parent client not found")

    offset = (page - 1) * limit

    # Get child clients
    stmt = select(ClientModel).where(
        ClientModel.tenant_id == tenant_id,
        ClientModel.parent_client_id == client_id,
        ClientModel.deleted_at.is_(None),
    )
    stmt = stmt.order_by(ClientModel.created_at.desc()).limit(limit).offset(offset)

    result = await db.execute(stmt)
    models = result.scalars().all()

    # Count total
    count_stmt = select(func.count(ClientModel.id)).where(
        ClientModel.tenant_id == tenant_id,
        ClientModel.parent_client_id == client_id,
        ClientModel.deleted_at.is_(None),
    )
    count_result = await db.execute(count_stmt)
    total = int(count_result.scalar() or 0)

    # Convert to entities and responses

    clients = [ClientMapper.to_entity(model) for model in models]

    return ClientListResponse(
        items=[_to_client_response(client) for client in clients],
        total=total,
        page=page,
        limit=limit,
        has_more=(offset + limit) < total,
    )
