"""
Client API Routes

FastAPI routes for Client operations.
Follows hybrid approach: Commands use use cases, Queries use repositories directly.
"""

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import get_client_repository, get_contract_repository, get_user_repository
from app.api.schemas.client_schemas import (
    AddressCreate,
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
    ContactInfoCreate,
    ContactInfoSchema,
)
from app.application.use_cases.client_use_cases import (
    ActivateClientUseCase,
    ArchiveClientUseCase,
    CreateClientUseCase,
    DeactivateClientUseCase,
    GetClientUseCase,
    RestoreClientUseCase,
    SuspendClientUseCase,
    TerminateClientUseCase,
    UpdateClientBillingAddressUseCase,
    UpdateClientContactInfoUseCase,
    UpdateClientUseCase,
    VerifyClientUseCase,
)
from app.core.database import get_db
from app.domain.enums import BaseStatus, ContactMethod, ContractStatus
from app.domain.entities.client import ClientEntity
from app.domain.exceptions import DomainError
from app.domain.repositories.client_repository import ClientRepository
from app.domain.repositories.contract_repository import ContractRepository
from app.domain.repositories.user_repository import UserRepository
from app.domain.value_objects.core import (
    Address,
    ClientId,
    ContactInfo,
    Email,
    IndustryId,
    TenantId,
    UserId,
)
from app.infrastructure.models.client_model import ClientModel
from app.infrastructure.models.contract_model import ContractModel
from sqlalchemy import func, select
from app.shared.utils.generators import generate_cuid
from app.shared.utils.http_errors import get_error_status_code

router = APIRouter(prefix="/clients", tags=["clients"])


def _to_client_response(client: ClientEntity) -> ClientResponse:
    """Map ClientEntity to API response."""
    contact_info = ContactInfoSchema(
        phone=client._contact_info.phone,
        email=client._contact_info.email.value if client._contact_info.email else None,
        address=client._contact_info.address,
    )

    billing_address = None
    if client._billing_address:
        billing_address = AddressSchema(
            street=client._billing_address.street,
            city=client._billing_address.city,
            country=client._billing_address.country,
            postal_code=client._billing_address.postal_code,
        )

    return ClientResponse(
        id=client._id.value,
        tenant_id=client._tenant_id.value,
        name=client._name,
        status=client._status,
        is_verified=client._is_verified,
        contact_info=contact_info,
        billing_address=billing_address,
        industry_id=client._industry_id.value if client._industry_id else None,
        parent_client_id=client._parent_client_id.value
        if client._parent_client_id
        else None,
        preferred_contact_method=client._preferred_contact_method,
        is_active=client.is_active(),
    )


# ==================== COMMANDS (Use Cases) ====================


@router.post(
    "/",
    response_model=ClientResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new client",
)
async def create_client(
    data: ClientCreate,
    tenant_id: str = Query(..., description="Tenant identifier"),
    client_repo: ClientRepository = Depends(get_client_repository),
    db: AsyncSession = Depends(get_db),
):
    """
    Create a new client.

    This is a COMMAND operation, so it uses a use case for orchestration.
    """
    try:
        # Convert schemas to value objects
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

        create_use_case = CreateClientUseCase(client_repo)

        client = await create_use_case.execute(
            client_id=ClientId(generate_cuid()),
            tenant_id=TenantId(tenant_id),
            name=data.name,
            contact_info=contact_info,
            billing_address=billing_address,
            industry_id=IndustryId(data.industry_id) if data.industry_id else None,
            parent_client_id=ClientId(data.parent_client_id)
            if data.parent_client_id
            else None,
        )

        await db.commit()

        return _to_client_response(client)
    except ValueError as e:
        await db.rollback()
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)) from e
    except DomainError as e:
        await db.rollback()
        status_code = get_error_status_code(str(e))
        raise HTTPException(status_code=status_code, detail=str(e)) from e


@router.post(
    "/{client_id}/verify",
    response_model=ClientResponse,
    summary="Verify a client",
)
async def verify_client(
    client_id: str,
    verified_by: str = Query(..., description="User ID who verified the client"),
    client_repo: ClientRepository = Depends(get_client_repository),
    db: AsyncSession = Depends(get_db),
):
    """
    Verify a client.

    This is a COMMAND operation, so it uses a use case for orchestration.
    """
    try:
        verify_use_case = VerifyClientUseCase(client_repo)

        client = await verify_use_case.execute(
            ClientId(client_id), UserId(verified_by)
        )

        await db.commit()

        return _to_client_response(client)
    except ValueError as e:
        await db.rollback()
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e)) from e
    except DomainError as e:
        await db.rollback()
        status_code = get_error_status_code(str(e))
        raise HTTPException(status_code=status_code, detail=str(e)) from e


@router.post(
    "/{client_id}/activate",
    response_model=ClientResponse,
    summary="Activate a client",
)
async def activate_client(
    client_id: str,
    client_repo: ClientRepository = Depends(get_client_repository),
    db: AsyncSession = Depends(get_db),
):
    """
    Activate a client.

    This is a COMMAND operation, so it uses a use case for orchestration.
    """
    try:
        activate_use_case = ActivateClientUseCase(client_repo)

        client = await activate_use_case.execute(ClientId(client_id))

        await db.commit()

        return _to_client_response(client)
    except ValueError as e:
        await db.rollback()
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e)) from e
    except DomainError as e:
        await db.rollback()
        status_code = get_error_status_code(str(e))
        raise HTTPException(status_code=status_code, detail=str(e)) from e


@router.post(
    "/{client_id}/deactivate",
    response_model=ClientResponse,
    summary="Deactivate a client",
)
async def deactivate_client(
    client_id: str,
    request: ClientDeactivateRequest,
    client_repo: ClientRepository = Depends(get_client_repository),
    db: AsyncSession = Depends(get_db),
):
    """
    Deactivate a client.

    This is a COMMAND operation, so it uses a use case for orchestration.
    """
    try:
        deactivate_use_case = DeactivateClientUseCase(client_repo)

        client = await deactivate_use_case.execute(
            ClientId(client_id), request.reason
        )

        await db.commit()

        return _to_client_response(client)
    except ValueError as e:
        await db.rollback()
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e)) from e
    except DomainError as e:
        await db.rollback()
        status_code = get_error_status_code(str(e))
        raise HTTPException(status_code=status_code, detail=str(e)) from e


@router.post(
    "/{client_id}/suspend",
    response_model=ClientResponse,
    summary="Suspend a client",
)
async def suspend_client(
    client_id: str,
    request: ClientSuspendRequest,
    client_repo: ClientRepository = Depends(get_client_repository),
    db: AsyncSession = Depends(get_db),
):
    """
    Suspend a client.

    This is a COMMAND operation, so it uses a use case for orchestration.
    """
    try:
        suspend_use_case = SuspendClientUseCase(client_repo)

        client = await suspend_use_case.execute(ClientId(client_id), request.reason)

        await db.commit()

        return _to_client_response(client)
    except ValueError as e:
        await db.rollback()
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e)) from e
    except DomainError as e:
        await db.rollback()
        status_code = get_error_status_code(str(e))
        raise HTTPException(status_code=status_code, detail=str(e)) from e


@router.post(
    "/{client_id}/terminate",
    response_model=ClientResponse,
    summary="Terminate a client",
)
async def terminate_client(
    client_id: str,
    request: ClientTerminateRequest,
    client_repo: ClientRepository = Depends(get_client_repository),
    db: AsyncSession = Depends(get_db),
):
    """
    Terminate a client.

    This is a COMMAND operation, so it uses a use case for orchestration.
    """
    try:
        terminate_use_case = TerminateClientUseCase(client_repo)

        client = await terminate_use_case.execute(ClientId(client_id), request.reason)

        await db.commit()

        return _to_client_response(client)
    except ValueError as e:
        await db.rollback()
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e)) from e
    except DomainError as e:
        await db.rollback()
        status_code = get_error_status_code(str(e))
        raise HTTPException(status_code=status_code, detail=str(e)) from e


@router.post(
    "/{client_id}/archive",
    response_model=ClientResponse,
    summary="Archive a client",
)
async def archive_client(
    client_id: str,
    client_repo: ClientRepository = Depends(get_client_repository),
    db: AsyncSession = Depends(get_db),
):
    """
    Archive a client.

    This is a COMMAND operation, so it uses a use case for orchestration.
    """
    try:
        archive_use_case = ArchiveClientUseCase(client_repo)

        client = await archive_use_case.execute(ClientId(client_id))

        await db.commit()

        return _to_client_response(client)
    except ValueError as e:
        await db.rollback()
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e)) from e
    except DomainError as e:
        await db.rollback()
        status_code = get_error_status_code(str(e))
        raise HTTPException(status_code=status_code, detail=str(e)) from e


@router.post(
    "/{client_id}/restore",
    response_model=ClientResponse,
    summary="Restore a client",
)
async def restore_client(
    client_id: str,
    client_repo: ClientRepository = Depends(get_client_repository),
    db: AsyncSession = Depends(get_db),
):
    """
    Restore an archived or soft-deleted client.

    This is a COMMAND operation, so it uses a use case for orchestration.
    """
    try:
        restore_use_case = RestoreClientUseCase(client_repo)

        client = await restore_use_case.execute(ClientId(client_id))

        await db.commit()

        return _to_client_response(client)
    except ValueError as e:
        await db.rollback()
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e)) from e
    except DomainError as e:
        await db.rollback()
        status_code = get_error_status_code(str(e))
        raise HTTPException(status_code=status_code, detail=str(e)) from e


@router.patch(
    "/{client_id}",
    response_model=ClientResponse,
    summary="Update client basic information",
)
async def update_client(
    client_id: str,
    data: ClientUpdate,
    client_repo: ClientRepository = Depends(get_client_repository),
    db: AsyncSession = Depends(get_db),
):
    """
    Update client basic information.

    This is a COMMAND operation, so it uses a use case for orchestration.
    """
    try:
        update_use_case = UpdateClientUseCase(client_repo)

        client = await update_use_case.execute(
            ClientId(client_id),
            name=data.name,
            preferred_contact_method=data.preferred_contact_method,
        )

        await db.commit()

        return _to_client_response(client)
    except ValueError as e:
        await db.rollback()
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e)) from e
    except DomainError as e:
        await db.rollback()
        status_code = get_error_status_code(str(e))
        raise HTTPException(status_code=status_code, detail=str(e)) from e


@router.patch(
    "/{client_id}/contact-info",
    response_model=ClientResponse,
    summary="Update client contact information",
)
async def update_client_contact_info(
    client_id: str,
    request: ClientUpdateContactInfo,
    client_repo: ClientRepository = Depends(get_client_repository),
    db: AsyncSession = Depends(get_db),
):
    """
    Update client contact information.

    This is a COMMAND operation, so it uses a use case for orchestration.
    """
    try:
        contact_info = ContactInfo(
            phone=request.contact_info.phone,
            email=Email(request.contact_info.email)
            if request.contact_info.email
            else None,
            address=request.contact_info.address,
        )

        update_use_case = UpdateClientContactInfoUseCase(client_repo)

        client = await update_use_case.execute(ClientId(client_id), contact_info)

        await db.commit()

        return _to_client_response(client)
    except ValueError as e:
        await db.rollback()
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e)) from e
    except DomainError as e:
        await db.rollback()
        status_code = get_error_status_code(str(e))
        raise HTTPException(status_code=status_code, detail=str(e)) from e


@router.patch(
    "/{client_id}/billing-address",
    response_model=ClientResponse,
    summary="Update client billing address",
)
async def update_client_billing_address(
    client_id: str,
    request: ClientUpdateBillingAddress,
    client_repo: ClientRepository = Depends(get_client_repository),
    db: AsyncSession = Depends(get_db),
):
    """
    Update client billing address.

    This is a COMMAND operation, so it uses a use case for orchestration.
    """
    try:
        billing_address = None
        if request.billing_address:
            billing_address = Address(
                street=request.billing_address.street,
                city=request.billing_address.city,
                country=request.billing_address.country,
                postal_code=request.billing_address.postal_code,
            )

        update_use_case = UpdateClientBillingAddressUseCase(client_repo)

        client = await update_use_case.execute(ClientId(client_id), billing_address)

        await db.commit()

        return _to_client_response(client)
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
    response_model=ClientListResponse,
    summary="List clients with filtering and pagination",
)
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
):
    """
    List clients with filtering, searching, and pagination.

    This is a QUERY operation, so it calls the repository directly.
    """
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

    client_responses = [_to_client_response(client) for client in clients]

    return ClientListResponse(
        items=client_responses,
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
async def get_client(
    client_id: str,
    client_repo: ClientRepository = Depends(get_client_repository),
):
    """
    Get client by ID.

    This is a QUERY operation, so it calls the repository directly.
    No use case needed for simple reads.
    """
    client = await client_repo.get_by_id(ClientId(client_id))

    if not client:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Client not found"
        )

    return _to_client_response(client)


@router.get(
    "/name/{name}",
    response_model=ClientResponse,
    summary="Get client by name",
)
async def get_client_by_name(
    name: str,
    tenant_id: str = Query(..., description="Tenant identifier"),
    client_repo: ClientRepository = Depends(get_client_repository),
):
    """
    Get client by name within a tenant.

    This is a QUERY operation, so it calls the repository directly.
    """
    client = await client_repo.get_by_name(TenantId(tenant_id), name)

    if not client:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Client not found"
        )

    return _to_client_response(client)


@router.get(
    "/check-name/{name}",
    summary="Check if client name is available",
)
async def check_name_availability(
    name: str,
    tenant_id: str = Query(..., description="Tenant identifier"),
    client_repo: ClientRepository = Depends(get_client_repository),
):
    """
    Check if a client name is available within a tenant.

    This is a QUERY operation, so it calls the repository directly.
    """
    client = await client_repo.get_by_name(TenantId(tenant_id), name)
    return {"available": client is None, "name": name, "tenant_id": tenant_id}


@router.get(
    "/{client_id}/stats",
    response_model=ClientStatsResponse,
    summary="Get client statistics",
)
async def get_client_stats(
    client_id: str,
    tenant_id: str = Query(..., description="Tenant identifier"),
    client_repo: ClientRepository = Depends(get_client_repository),
    contract_repo: ContractRepository = Depends(get_contract_repository),
    db: AsyncSession = Depends(get_db),
):
    """
    Get client statistics including child clients and contracts.

    This is a QUERY operation that aggregates data from multiple repositories.
    """
    client = await client_repo.get_by_id(ClientId(client_id))

    if not client:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Client not found"
        )

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
        is_verified=client._is_verified,
        status=client._status,
    )


@router.get(
    "/{client_id}/children",
    response_model=ClientListResponse,
    summary="Get child clients of a parent client",
)
async def get_child_clients(
    client_id: str,
    tenant_id: str = Query(..., description="Tenant identifier"),
    page: int = Query(1, ge=1, description="Page number"),
    limit: int = Query(20, ge=1, le=100, description="Items per page"),
    client_repo: ClientRepository = Depends(get_client_repository),
    db: AsyncSession = Depends(get_db),
):
    """
    Get all child clients of a parent client.

    This is a QUERY operation, so it calls the repository directly.
    """
    # Verify parent client exists
    parent = await client_repo.get_by_id(ClientId(client_id))
    if not parent:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Parent client not found"
        )

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
    from app.infrastructure.mappers.client_mapper import ClientMapper

    clients = [ClientMapper.to_entity(model) for model in models]
    client_responses = [_to_client_response(client) for client in clients]

    return ClientListResponse(
        items=client_responses,
        total=total,
        page=page,
        limit=limit,
        has_more=(offset + limit) < total,
    )
