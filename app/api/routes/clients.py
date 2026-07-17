"""
Client API Routes

FastAPI routes for Client operations.
Follows hybrid approach: Commands use use cases, Queries use repositories directly.
Refactored to use @transactional decorator to eliminate try/except boilerplate.
"""

from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import (
    get_audit_event_handler,
    get_client_repository,
    get_contract_repository,
    get_tenant_repository,
)
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
    ClientUpdateTier,
    ContactInfoSchema,
)
from app.application.use_cases.client_use_cases import (
    CreateClientUseCase,
    UpdateClientUseCase,
)
from app.application.use_cases.transitions import (
    ClientTransition,
    TransitionUseCase,
)
from app.core.authorization import (
    get_client_for_current_tenant,
    require_same_tenant,
)
from app.core.database import get_db
from app.core.security import TokenData, get_current_user
from app.domain.entities.client import ClientEntity
from app.domain.enums import BaseStatus, ClientTier
from app.domain.exceptions import EvexiaException
from app.domain.repositories.client_repository import ClientRepository
from app.domain.repositories.contract_repository import ContractRepository
from app.domain.repositories.tenant_repository import TenantRepository
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
from app.shared.decorators import readonly, transactional
from app.shared.utils.generators import generate_cuid
from app.shared.utils.route_audit_helper import audit_entity_operation

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
        code=client.code,
        status=client.status,
        is_verified=client.is_verified,
        contact_info=contact_info,
        billing_address=billing_address,
        industry_id=client.industry_id.value if client.industry_id else None,
        parent_client_id=client.parent_client_id.value if client.parent_client_id else None,
        preferred_contact_method=client.preferred_contact_method,
        tier=client.tier,
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
    request: Request,
    tenant_id: str = Query(..., description="Tenant identifier"),
    current_user: TokenData = Depends(require_same_tenant),
    client_repo: ClientRepository = Depends(get_client_repository),
    tenant_repo: TenantRepository = Depends(get_tenant_repository),
    audit_handler=Depends(get_audit_event_handler),
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

    try:
        client = await CreateClientUseCase(client_repo, tenant_repo).execute(
            client_id=ClientId(generate_cuid()),
            tenant_id=TenantId(tenant_id),
            name=data.name,
            code=data.code,
            contact_info=contact_info,
            billing_address=billing_address,
            industry_id=IndustryId(data.industry_id) if data.industry_id else None,
            parent_client_id=ClientId(data.parent_client_id) if data.parent_client_id else None,
        )
    except EvexiaException as e:
        raise HTTPException(status_code=e.http_status, detail=e.message) from e

    await audit_entity_operation(
        entity=client,
        audit_handler=audit_handler,
        tenant_id=tenant_id,
        user_id=current_user.user_id,
        request=request,
    )
    return _to_client_response(client)


@router.post(
    "/{client_id}/verify",
    response_model=ClientResponse,
    summary="Verify a client",
)
@transactional()
async def verify_client(
    request: Request,
    verified_by: str = Query(..., description="User ID who verified the client"),
    current_user: TokenData = Depends(get_current_user),
    client: ClientEntity = Depends(get_client_for_current_tenant),
    client_repo: ClientRepository = Depends(get_client_repository),
    audit_handler=Depends(get_audit_event_handler),
    db: AsyncSession = Depends(get_db),
):
    """Verify a client."""
    use_case: TransitionUseCase = TransitionUseCase(client_repo)
    use_case.entity_name = "Client"
    client = await use_case.execute(
        client.id, ClientTransition.VERIFY, verified_by=UserId(verified_by)
    )
    await audit_entity_operation(
        entity=client,
        audit_handler=audit_handler,
        tenant_id=client.tenant_id,
        user_id=current_user.user_id,
        request=request,
    )
    return _to_client_response(client)


@router.post(
    "/{client_id}/activate",
    response_model=ClientResponse,
    summary="Activate a client",
)
@transactional()
async def activate_client(
    request: Request,
    current_user: TokenData = Depends(get_current_user),
    client: ClientEntity = Depends(get_client_for_current_tenant),
    client_repo: ClientRepository = Depends(get_client_repository),
    audit_handler=Depends(get_audit_event_handler),
    db: AsyncSession = Depends(get_db),
):
    """Activate a client."""
    use_case: TransitionUseCase = TransitionUseCase(client_repo)
    use_case.entity_name = "Client"
    client = await use_case.execute(client.id, ClientTransition.ACTIVATE)
    await audit_entity_operation(
        entity=client,
        audit_handler=audit_handler,
        tenant_id=client.tenant_id,
        user_id=current_user.user_id,
        request=request,
    )
    return _to_client_response(client)


@router.post(
    "/{client_id}/deactivate",
    response_model=ClientResponse,
    summary="Deactivate a client",
)
@transactional()
async def deactivate_client(
    request: Request,
    body: ClientDeactivateRequest,
    current_user: TokenData = Depends(get_current_user),
    client: ClientEntity = Depends(get_client_for_current_tenant),
    client_repo: ClientRepository = Depends(get_client_repository),
    audit_handler=Depends(get_audit_event_handler),
    db: AsyncSession = Depends(get_db),
):
    """Deactivate a client."""
    use_case: TransitionUseCase = TransitionUseCase(client_repo)
    use_case.entity_name = "Client"
    client = await use_case.execute(client.id, ClientTransition.DEACTIVATE, reason=body.reason)
    await audit_entity_operation(
        entity=client,
        audit_handler=audit_handler,
        tenant_id=client.tenant_id,
        user_id=current_user.user_id,
        request=request,
    )
    return _to_client_response(client)


@router.post(
    "/{client_id}/suspend",
    response_model=ClientResponse,
    summary="Suspend a client",
)
@transactional()
async def suspend_client(
    request: Request,
    body: ClientSuspendRequest,
    current_user: TokenData = Depends(get_current_user),
    client: ClientEntity = Depends(get_client_for_current_tenant),
    client_repo: ClientRepository = Depends(get_client_repository),
    audit_handler=Depends(get_audit_event_handler),
    db: AsyncSession = Depends(get_db),
):
    """Suspend a client."""
    use_case: TransitionUseCase = TransitionUseCase(client_repo)
    use_case.entity_name = "Client"
    client = await use_case.execute(client.id, ClientTransition.SUSPEND, reason=body.reason)
    await audit_entity_operation(
        entity=client,
        audit_handler=audit_handler,
        tenant_id=client.tenant_id,
        user_id=current_user.user_id,
        request=request,
    )
    return _to_client_response(client)


@router.post(
    "/{client_id}/terminate",
    response_model=ClientResponse,
    summary="Terminate a client",
)
@transactional()
async def terminate_client(
    request: Request,
    body: ClientTerminateRequest,
    current_user: TokenData = Depends(get_current_user),
    client: ClientEntity = Depends(get_client_for_current_tenant),
    client_repo: ClientRepository = Depends(get_client_repository),
    audit_handler=Depends(get_audit_event_handler),
    db: AsyncSession = Depends(get_db),
):
    """Terminate a client."""
    use_case: TransitionUseCase = TransitionUseCase(client_repo)
    use_case.entity_name = "Client"
    client = await use_case.execute(client.id, ClientTransition.TERMINATE, reason=body.reason)
    await audit_entity_operation(
        entity=client,
        audit_handler=audit_handler,
        tenant_id=client.tenant_id,
        user_id=current_user.user_id,
        request=request,
    )
    return _to_client_response(client)


@router.post(
    "/{client_id}/archive",
    response_model=ClientResponse,
    summary="Archive a client",
)
@transactional()
async def archive_client(
    request: Request,
    current_user: TokenData = Depends(get_current_user),
    client: ClientEntity = Depends(get_client_for_current_tenant),
    client_repo: ClientRepository = Depends(get_client_repository),
    audit_handler=Depends(get_audit_event_handler),
    db: AsyncSession = Depends(get_db),
):
    """Archive a client."""
    use_case: TransitionUseCase = TransitionUseCase(client_repo)
    use_case.entity_name = "Client"
    client = await use_case.execute(client.id, ClientTransition.ARCHIVE)
    await audit_entity_operation(
        entity=client,
        audit_handler=audit_handler,
        tenant_id=client.tenant_id,
        user_id=current_user.user_id,
        request=request,
    )
    return _to_client_response(client)


@router.post(
    "/{client_id}/restore",
    response_model=ClientResponse,
    summary="Restore a client",
)
@transactional()
async def restore_client(
    request: Request,
    current_user: TokenData = Depends(get_current_user),
    client: ClientEntity = Depends(get_client_for_current_tenant),
    client_repo: ClientRepository = Depends(get_client_repository),
    audit_handler=Depends(get_audit_event_handler),
    db: AsyncSession = Depends(get_db),
):
    """Restore an archived or soft-deleted client."""
    use_case: TransitionUseCase = TransitionUseCase(client_repo)
    use_case.entity_name = "Client"
    client = await use_case.execute(client.id, ClientTransition.RESTORE)
    await audit_entity_operation(
        entity=client,
        audit_handler=audit_handler,
        tenant_id=client.tenant_id,
        user_id=current_user.user_id,
        request=request,
    )
    return _to_client_response(client)


@router.patch(
    "/{client_id}",
    response_model=ClientResponse,
    summary="Update client basic information",
)
@transactional()
async def update_client(
    data: ClientUpdate,
    request: Request,
    current_user: TokenData = Depends(get_current_user),
    client: ClientEntity = Depends(get_client_for_current_tenant),
    client_repo: ClientRepository = Depends(get_client_repository),
    audit_handler=Depends(get_audit_event_handler),
    db: AsyncSession = Depends(get_db),
):
    """Update client basic information."""
    client = await UpdateClientUseCase(client_repo).execute(
        client.id,
        name=data.name,
        preferred_contact_method=data.preferred_contact_method,
        tier=data.tier,
    )
    await audit_entity_operation(
        entity=client,
        audit_handler=audit_handler,
        tenant_id=client.tenant_id,
        user_id=current_user.user_id,
        request=request,
    )
    return _to_client_response(client)


@router.patch(
    "/{client_id}/contact-info",
    response_model=ClientResponse,
    summary="Update client contact information",
)
@transactional()
async def update_client_contact_info(
    data: ClientUpdateContactInfo,
    request: Request,
    current_user: TokenData = Depends(get_current_user),
    client: ClientEntity = Depends(get_client_for_current_tenant),
    client_repo: ClientRepository = Depends(get_client_repository),
    audit_handler=Depends(get_audit_event_handler),
    db: AsyncSession = Depends(get_db),
):
    """Update client contact information."""
    contact_info = ContactInfo(
        phone=data.contact_info.phone,
        email=Email(data.contact_info.email) if data.contact_info.email else None,
        address=data.contact_info.address,
    )

    use_case: TransitionUseCase = TransitionUseCase(client_repo)
    use_case.entity_name = "Client"
    client = await use_case.execute(
        client.id, ClientTransition.UPDATE_CONTACT_INFO, contact_info=contact_info
    )
    await audit_entity_operation(
        entity=client,
        audit_handler=audit_handler,
        tenant_id=client.tenant_id,
        user_id=current_user.user_id,
        request=request,
    )
    return _to_client_response(client)


@router.patch(
    "/{client_id}/billing-address",
    response_model=ClientResponse,
    summary="Update client billing address",
)
@transactional()
async def update_client_billing_address(
    data: ClientUpdateBillingAddress,
    request: Request,
    current_user: TokenData = Depends(get_current_user),
    client: ClientEntity = Depends(get_client_for_current_tenant),
    client_repo: ClientRepository = Depends(get_client_repository),
    audit_handler=Depends(get_audit_event_handler),
    db: AsyncSession = Depends(get_db),
):
    """Update client billing address."""
    billing_address = None
    if data.billing_address:
        billing_address = Address(
            street=data.billing_address.street,
            city=data.billing_address.city,
            country=data.billing_address.country,
            postal_code=data.billing_address.postal_code,
        )

    use_case: TransitionUseCase = TransitionUseCase(client_repo)
    use_case.entity_name = "Client"
    client = await use_case.execute(
        client.id, ClientTransition.UPDATE_BILLING_ADDRESS, billing_address=billing_address
    )
    await audit_entity_operation(
        entity=client,
        audit_handler=audit_handler,
        tenant_id=client.tenant_id,
        user_id=current_user.user_id,
        request=request,
    )
    return _to_client_response(client)


@router.patch(
    "/{client_id}/tier",
    response_model=ClientResponse,
    summary="Set client engagement tier (A/B/C)",
)
@transactional()
async def update_client_tier(
    data: ClientUpdateTier,
    request: Request,
    current_user: TokenData = Depends(get_current_user),
    client: ClientEntity = Depends(get_client_for_current_tenant),
    client_repo: ClientRepository = Depends(get_client_repository),
    audit_handler=Depends(get_audit_event_handler),
    db: AsyncSession = Depends(get_db),
):
    """Set the client's engagement tier."""
    use_case: TransitionUseCase = TransitionUseCase(client_repo)
    use_case.entity_name = "Client"
    client = await use_case.execute(
        client.id, ClientTransition.UPDATE_TIER, tier=data.tier
    )
    await audit_entity_operation(
        entity=client,
        audit_handler=audit_handler,
        tenant_id=client.tenant_id,
        user_id=current_user.user_id,
        request=request,
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
    tier: ClientTier | None = Query(None, description="Filter by engagement tier (A/B/C)"),
    search: str | None = Query(None, description="Search in client name"),
    page: int = Query(1, ge=1, description="Page number"),
    limit: int = Query(20, ge=1, le=100, description="Items per page"),
    sort_by: str = Query("created_at", description="Field to sort by"),
    sort_desc: bool = Query(True, description="Sort in descending order"),
    current_user: TokenData = Depends(require_same_tenant),
    client_repo: ClientRepository = Depends(get_client_repository),
    db: AsyncSession = Depends(get_db),
):
    """List clients with filtering, searching, and pagination."""
    offset = (page - 1) * limit

    clients = await client_repo.list_all(
        tenant_id=TenantId(tenant_id),
        status=status,
        is_verified=is_verified,
        tier=tier,
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
        tier=tier,
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
    client: ClientEntity = Depends(get_client_for_current_tenant),
    db: AsyncSession = Depends(get_db),
):
    """Get client by ID."""
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
    current_user: TokenData = Depends(require_same_tenant),
    client_repo: ClientRepository = Depends(get_client_repository),
    db: AsyncSession = Depends(get_db),
):
    """Get client by name within a tenant."""
    client = await client_repo.get_by_name(TenantId(tenant_id), name)
    if not client:
        raise HTTPException(status_code=404, detail="Client not found")
    return _to_client_response(client)


@router.get(
    "/check-name/{name}",
    summary="Check if client name is available",
)
@readonly()
async def check_name_availability(
    name: str,
    tenant_id: str = Query(..., description="Tenant identifier"),
    current_user: TokenData = Depends(require_same_tenant),
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
    client: ClientEntity = Depends(get_client_for_current_tenant),
    client_repo: ClientRepository = Depends(get_client_repository),
    contract_repo: ContractRepository = Depends(get_contract_repository),
    db: AsyncSession = Depends(get_db),
):
    """Get client statistics including child clients and contracts."""
    tenant_id = client.tenant_id.value
    client_id = client.id.value

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
        client.tenant_id, client.id
    )
    total_contracts_count = len(contracts)

    # Count active contracts
    active_contract = await contract_repo.get_active_by_client_id(
        client.tenant_id, client.id
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
    parent: ClientEntity = Depends(get_client_for_current_tenant),
    page: int = Query(1, ge=1, description="Page number"),
    limit: int = Query(20, ge=1, le=100, description="Items per page"),
    client_repo: ClientRepository = Depends(get_client_repository),
    db: AsyncSession = Depends(get_db),
):
    """Get all child clients of a parent client."""
    tenant_id = parent.tenant_id.value
    client_id = parent.id.value
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

    clients = [ClientMapper.to_entity(model) for model in models]

    return ClientListResponse(
        items=[_to_client_response(c) for c in clients],
        total=total,
        page=page,
        limit=limit,
        has_more=(offset + limit) < total,
    )
