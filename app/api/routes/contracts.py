"""
Contract API Routes

FastAPI routes for Contract operations.
Refactored to use @transactional decorator to eliminate try/except boilerplate.
"""

import decimal

from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import TokenData, get_current_user

from app.api.dependencies import get_audit_event_handler, get_contract_repository
from app.api.schemas.contract_schemas import (
    ContractCreate,
    ContractListResponse,
    ContractRenewRequest,
    ContractResponse,
    ContractSignRequest,
    ContractTerminateRequest,
    ContractUpdate,
    ContractUpdatePaymentStatus,
    DateRangeSchema,
    MoneySchema,
)
from app.application.use_cases.contract_use_cases import (
    ActivateContractUseCase,
    ArchiveContractUseCase,
    CreateContractUseCase,
    GetContractUseCase,
    RenewContractUseCase,
    RestoreContractUseCase,
    SignContractUseCase,
    TerminateContractUseCase,
    UpdateContractPaymentStatusUseCase,
    UpdateContractUseCase,
)
from app.core.database import get_db
from app.domain.enums import ContractStatus, PaymentStatus
from app.domain.entities.contract import ContractEntity
from app.domain.repositories.contract_repository import ContractRepository
from app.domain.value_objects.core import (
    ClientId,
    ContractId,
    Money,
    TenantId,
)
from app.shared.decorators import transactional, readonly
from app.shared.utils.generators import generate_cuid
from app.shared.utils.route_audit_helper import audit_entity_operation

router = APIRouter(prefix="/contracts", tags=["contracts"])


def _to_contract_response(contract: ContractEntity) -> ContractResponse:
    """Map ContractEntity to API response using public properties."""
    period = DateRangeSchema(
        start_date=contract.period.start_date,
        end_date=contract.period.end_date,
    )

    billing_rate = MoneySchema(
        amount=str(contract.billing_rate.amount),
        currency=contract.billing_rate.currency,
    )

    return ContractResponse(
        id=contract.id.value,
        tenant_id=contract.tenant_id.value,
        client_id=contract.client_id.value,
        period=period,
        billing_rate=billing_rate,
        payment_frequency=contract.payment_frequency,
        payment_status=contract.payment_status,
        status=contract.status,
        is_auto_renew=contract.is_auto_renew,
        last_billing_date=contract.last_billing_date,
        next_billing_date=contract.next_billing_date,
        signed_by=contract.signed_by,
        signed_at=contract.signed_at,
        termination_reason=contract.termination_reason,
        is_active=contract.is_active(),
        days_remaining=contract.days_remaining(),
    )


# ==================== COMMANDS (Use Cases) ====================


@router.post(
    "/",
    response_model=ContractResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new contract",
)
@transactional()
async def create_contract(
    data: ContractCreate,
    request: Request,
    tenant_id: str = Query(..., description="Tenant identifier"),
    current_user: TokenData = Depends(get_current_user),
    contract_repo: ContractRepository = Depends(get_contract_repository),
    audit_handler=Depends(get_audit_event_handler),
    db: AsyncSession = Depends(get_db),
):
    """Create a new contract."""
    if current_user.tenant_id != tenant_id:
        raise HTTPException(status_code=403, detail="Access denied to this tenant")
    billing_rate = Money(
        amount=decimal.Decimal(data.billing_rate.amount),
        currency=data.billing_rate.currency,
    )

    contract = await CreateContractUseCase(contract_repo).execute(
        contract_id=ContractId(generate_cuid()),
        tenant_id=TenantId(tenant_id),
        client_id=ClientId(data.client_id),
        start_date=data.start_date,
        end_date=data.end_date,
        billing_rate=billing_rate,
        payment_frequency=data.payment_frequency,
        is_auto_renew=data.is_auto_renew,
    )
    await audit_entity_operation(
        entity=contract,
        audit_handler=audit_handler,
        tenant_id=tenant_id,
        user_id=current_user.user_id,
        request=request,
    )
    return _to_contract_response(contract)


@router.post(
    "/{contract_id}/activate",
    response_model=ContractResponse,
    summary="Activate a contract",
)
@transactional()
async def activate_contract(
    contract_id: str,
    request: Request,
    current_user: TokenData = Depends(get_current_user),
    contract_repo: ContractRepository = Depends(get_contract_repository),
    audit_handler=Depends(get_audit_event_handler),
    db: AsyncSession = Depends(get_db),
):
    """Activate a contract."""
    contract = await ActivateContractUseCase(contract_repo).execute(
        ContractId(contract_id)
    )
    await audit_entity_operation(
        entity=contract,
        audit_handler=audit_handler,
        tenant_id=contract.tenant_id,
        user_id=current_user.user_id,
        request=request,
    )
    return _to_contract_response(contract)


@router.post(
    "/{contract_id}/sign",
    response_model=ContractResponse,
    summary="Sign a contract",
)
@transactional()
async def sign_contract(
    contract_id: str,
    request: Request,
    body: ContractSignRequest,
    current_user: TokenData = Depends(get_current_user),
    contract_repo: ContractRepository = Depends(get_contract_repository),
    audit_handler=Depends(get_audit_event_handler),
    db: AsyncSession = Depends(get_db),
):
    """Sign a contract."""
    contract = await SignContractUseCase(contract_repo).execute(
        ContractId(contract_id), body.signed_by
    )
    await audit_entity_operation(
        entity=contract,
        audit_handler=audit_handler,
        tenant_id=contract.tenant_id,
        user_id=current_user.user_id,
        request=request,
    )
    return _to_contract_response(contract)


@router.post(
    "/{contract_id}/renew",
    response_model=ContractResponse,
    summary="Renew a contract",
)
@transactional()
async def renew_contract(
    contract_id: str,
    request: Request,
    body: ContractRenewRequest,
    current_user: TokenData = Depends(get_current_user),
    contract_repo: ContractRepository = Depends(get_contract_repository),
    audit_handler=Depends(get_audit_event_handler),
    db: AsyncSession = Depends(get_db),
):
    """Renew a contract."""
    new_rate = None
    if body.new_rate:
        new_rate = Money(
            amount=decimal.Decimal(body.new_rate.amount),
            currency=body.new_rate.currency,
        )

    # Convert datetime to date for renew method
    new_end_date = body.new_end_date.date()

    contract = await RenewContractUseCase(contract_repo).execute(
        ContractId(contract_id), new_end_date, new_rate
    )
    await audit_entity_operation(
        entity=contract,
        audit_handler=audit_handler,
        tenant_id=contract.tenant_id,
        user_id=current_user.user_id,
        request=request,
    )
    return _to_contract_response(contract)


@router.post(
    "/{contract_id}/terminate",
    response_model=ContractResponse,
    summary="Terminate a contract",
)
@transactional()
async def terminate_contract(
    contract_id: str,
    request: Request,
    body: ContractTerminateRequest,
    current_user: TokenData = Depends(get_current_user),
    contract_repo: ContractRepository = Depends(get_contract_repository),
    audit_handler=Depends(get_audit_event_handler),
    db: AsyncSession = Depends(get_db),
):
    """Terminate a contract."""
    contract = await TerminateContractUseCase(contract_repo).execute(
        ContractId(contract_id), body.reason
    )
    await audit_entity_operation(
        entity=contract,
        audit_handler=audit_handler,
        tenant_id=contract.tenant_id,
        user_id=current_user.user_id,
        request=request,
    )
    return _to_contract_response(contract)


@router.post(
    "/{contract_id}/archive",
    response_model=ContractResponse,
    summary="Archive a contract",
)
@transactional()
async def archive_contract(
    contract_id: str,
    request: Request,
    current_user: TokenData = Depends(get_current_user),
    contract_repo: ContractRepository = Depends(get_contract_repository),
    audit_handler=Depends(get_audit_event_handler),
    db: AsyncSession = Depends(get_db),
):
    """Archive a contract."""
    contract = await ArchiveContractUseCase(contract_repo).execute(
        ContractId(contract_id)
    )
    await audit_entity_operation(
        entity=contract,
        audit_handler=audit_handler,
        tenant_id=contract.tenant_id,
        user_id=current_user.user_id,
        request=request,
    )
    return _to_contract_response(contract)


@router.post(
    "/{contract_id}/restore",
    response_model=ContractResponse,
    summary="Restore a contract",
)
@transactional()
async def restore_contract(
    contract_id: str,
    request: Request,
    current_user: TokenData = Depends(get_current_user),
    contract_repo: ContractRepository = Depends(get_contract_repository),
    audit_handler=Depends(get_audit_event_handler),
    db: AsyncSession = Depends(get_db),
):
    """Restore a terminated or expired contract."""
    contract = await RestoreContractUseCase(contract_repo).execute(
        ContractId(contract_id)
    )
    await audit_entity_operation(
        entity=contract,
        audit_handler=audit_handler,
        tenant_id=contract.tenant_id,
        user_id=current_user.user_id,
        request=request,
    )
    return _to_contract_response(contract)


@router.patch(
    "/{contract_id}",
    response_model=ContractResponse,
    summary="Update contract information",
)
@transactional()
async def update_contract(
    contract_id: str,
    data: ContractUpdate,
    request: Request,
    current_user: TokenData = Depends(get_current_user),
    contract_repo: ContractRepository = Depends(get_contract_repository),
    audit_handler=Depends(get_audit_event_handler),
    db: AsyncSession = Depends(get_db),
):
    """Update contract information."""
    billing_rate = None
    if data.billing_rate:
        billing_rate = Money(
            amount=decimal.Decimal(data.billing_rate.amount),
            currency=data.billing_rate.currency,
        )

    contract = await UpdateContractUseCase(contract_repo).execute(
        ContractId(contract_id),
        billing_rate=billing_rate,
        payment_frequency=data.payment_frequency,
        is_auto_renew=data.is_auto_renew,
    )
    await audit_entity_operation(
        entity=contract,
        audit_handler=audit_handler,
        tenant_id=contract.tenant_id,
        user_id=current_user.user_id,
        request=request,
    )
    return _to_contract_response(contract)


@router.patch(
    "/{contract_id}/payment-status",
    response_model=ContractResponse,
    summary="Update contract payment status",
)
@transactional()
async def update_contract_payment_status(
    contract_id: str,
    request: Request,
    body: ContractUpdatePaymentStatus,
    current_user: TokenData = Depends(get_current_user),
    contract_repo: ContractRepository = Depends(get_contract_repository),
    audit_handler=Depends(get_audit_event_handler),
    db: AsyncSession = Depends(get_db),
):
    """Update contract payment status."""
    contract = await UpdateContractPaymentStatusUseCase(contract_repo).execute(
        ContractId(contract_id), body.payment_status
    )
    await audit_entity_operation(
        entity=contract,
        audit_handler=audit_handler,
        tenant_id=contract.tenant_id,
        user_id=current_user.user_id,
        request=request,
    )
    return _to_contract_response(contract)


# ==================== QUERIES (Direct Repository) ====================


@router.get(
    "/",
    response_model=ContractListResponse,
    summary="List contracts with filtering and pagination",
)
@readonly()
async def list_contracts(
    tenant_id: str = Query(..., description="Tenant identifier"),
    current_user: TokenData = Depends(get_current_user),
    client_id: str | None = Query(None, description="Filter by client identifier"),
    status: ContractStatus | None = Query(None, description="Filter by contract status"),
    payment_status: PaymentStatus | None = Query(
        None, description="Filter by payment status"
    ),
    page: int = Query(1, ge=1, description="Page number"),
    limit: int = Query(20, ge=1, le=100, description="Items per page"),
    sort_by: str = Query("created_at", description="Field to sort by"),
    sort_desc: bool = Query(True, description="Sort in descending order"),
    contract_repo: ContractRepository = Depends(get_contract_repository),
    db: AsyncSession = Depends(get_db),
):
    """List contracts with filtering, searching, and pagination."""
    if current_user.tenant_id != tenant_id:
        raise HTTPException(status_code=403, detail="Access denied to this tenant")
    offset = (page - 1) * limit

    contracts = await contract_repo.list_all(
        tenant_id=TenantId(tenant_id),
        client_id=ClientId(client_id) if client_id else None,
        status=status,
        payment_status=payment_status,
        limit=limit,
        offset=offset,
        sort_by=sort_by,
        sort_desc=sort_desc,
    )

    total = await contract_repo.count(
        tenant_id=TenantId(tenant_id),
        client_id=ClientId(client_id) if client_id else None,
        status=status,
        payment_status=payment_status,
    )

    return ContractListResponse(
        items=[_to_contract_response(contract) for contract in contracts],
        total=total,
        page=page,
        limit=limit,
        has_more=(offset + limit) < total,
    )


@router.get(
    "/{contract_id}",
    response_model=ContractResponse,
    summary="Get contract by ID",
)
@readonly()
async def get_contract(
    contract_id: str,
    contract_repo: ContractRepository = Depends(get_contract_repository),
    db: AsyncSession = Depends(get_db),
):
    """Get contract by ID."""
    contract = await contract_repo.get_by_id(ContractId(contract_id))
    if not contract:
        raise ValueError("Contract not found")
    return _to_contract_response(contract)


@router.get(
    "/client/{client_id}",
    response_model=list[ContractResponse],
    summary="Get all contracts for a client",
)
@readonly()
async def get_contracts_by_client(
    client_id: str,
    tenant_id: str = Query(..., description="Tenant identifier"),
    current_user: TokenData = Depends(get_current_user),
    contract_repo: ContractRepository = Depends(get_contract_repository),
    db: AsyncSession = Depends(get_db),
):
    """Get all contracts for a client."""
    if current_user.tenant_id != tenant_id:
        raise HTTPException(status_code=403, detail="Access denied to this tenant")
    contracts = await GetContractUseCase(contract_repo).execute_by_client(
        TenantId(tenant_id), ClientId(client_id)
    )
    return [_to_contract_response(contract) for contract in contracts]


@router.get(
    "/client/{client_id}/active",
    response_model=ContractResponse,
    summary="Get active contract for a client",
)
@readonly()
async def get_active_contract_by_client(
    client_id: str,
    tenant_id: str = Query(..., description="Tenant identifier"),
    current_user: TokenData = Depends(get_current_user),
    contract_repo: ContractRepository = Depends(get_contract_repository),
    db: AsyncSession = Depends(get_db),
):
    """Get active contract for a client."""
    if current_user.tenant_id != tenant_id:
        raise HTTPException(status_code=403, detail="Access denied to this tenant")
    contract = await GetContractUseCase(contract_repo).execute_active_by_client(
        TenantId(tenant_id), ClientId(client_id)
    )
    if not contract:
        raise ValueError("Active contract not found for this client")
    return _to_contract_response(contract)
