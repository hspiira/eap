"""
Contract API Routes

FastAPI routes for Contract operations.
Refactored to use @transactional decorator to eliminate try/except boilerplate.
"""

import decimal
from datetime import date

from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from sqlalchemy import Date, and_, cast, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import (
    PageParams,
    get_audit_event_handler,
    get_contract_repository,
    pagination,
)
from app.api.schemas.contract_schemas import (
    ContractCreate,
    ContractListResponse,
    ContractMetricsItem,
    ContractMetricsResponse,
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
    CreateContractUseCase,
    GetContractUseCase,
    UpdateContractUseCase,
)
from app.application.use_cases.transitions import (
    ContractTransition,
    TransitionUseCase,
)
from app.core.authorization import (
    get_contract_for_current_tenant,
    require_same_tenant,
)
from app.core.database import get_db
from app.core.security import TokenData, get_current_user
from app.domain.entities.contract import ContractEntity
from app.domain.enums import ContractStatus, PaymentStatus, SessionStatus
from app.domain.repositories.contract_repository import ContractRepository
from app.domain.value_objects.core import (
    ClientId,
    ContractId,
    Money,
    TenantId,
)
from app.infrastructure.models import (
    ContractModel,
    ServiceAssignmentModel,
    ServiceSessionModel,
)
from app.shared.decorators import readonly, transactional
from app.shared.utils.generators import generate_cuid
from app.shared.utils.route_audit_helper import audit_change

router = APIRouter(prefix="/contracts", tags=["contracts"])

SESSION_RATE_CURRENCY = "UGX"


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
    current_user: TokenData = Depends(require_same_tenant),
    contract_repo: ContractRepository = Depends(get_contract_repository),
    audit_handler=Depends(get_audit_event_handler),
    db: AsyncSession = Depends(get_db),
):
    """Create a new contract."""
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
    await audit_change(contract, audit_handler, current_user, request, tenant_id=tenant_id)
    return _to_contract_response(contract)


@router.post(
    "/{contract_id}/activate",
    response_model=ContractResponse,
    summary="Activate a contract",
)
@transactional()
async def activate_contract(
    request: Request,
    current_user: TokenData = Depends(get_current_user),
    contract: ContractEntity = Depends(get_contract_for_current_tenant),
    contract_repo: ContractRepository = Depends(get_contract_repository),
    audit_handler=Depends(get_audit_event_handler),
    db: AsyncSession = Depends(get_db),
):
    """Activate a contract."""
    use_case = TransitionUseCase(contract_repo, "Contract")
    contract = await use_case.execute(
        contract.id, ContractTransition.ACTIVATE, tenant_id=current_user.tenant_id
    )
    await audit_change(contract, audit_handler, current_user, request)
    return _to_contract_response(contract)


@router.post(
    "/{contract_id}/sign",
    response_model=ContractResponse,
    summary="Sign a contract",
)
@transactional()
async def sign_contract(
    request: Request,
    body: ContractSignRequest,
    current_user: TokenData = Depends(get_current_user),
    contract: ContractEntity = Depends(get_contract_for_current_tenant),
    contract_repo: ContractRepository = Depends(get_contract_repository),
    audit_handler=Depends(get_audit_event_handler),
    db: AsyncSession = Depends(get_db),
):
    """Sign a contract."""
    use_case = TransitionUseCase(contract_repo, "Contract")
    contract = await use_case.execute(
        contract.id,
        ContractTransition.SIGN,
        signed_by=body.signed_by,
        tenant_id=current_user.tenant_id,
    )
    await audit_change(contract, audit_handler, current_user, request)
    return _to_contract_response(contract)


@router.post(
    "/{contract_id}/renew",
    response_model=ContractResponse,
    summary="Renew a contract",
)
@transactional()
async def renew_contract(
    request: Request,
    body: ContractRenewRequest,
    current_user: TokenData = Depends(get_current_user),
    contract: ContractEntity = Depends(get_contract_for_current_tenant),
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

    use_case = TransitionUseCase(contract_repo, "Contract")
    contract = await use_case.execute(
        contract.id,
        ContractTransition.RENEW,
        new_end_date=body.new_end_date,
        new_rate=new_rate,
        tenant_id=current_user.tenant_id,
    )
    await audit_change(contract, audit_handler, current_user, request)
    return _to_contract_response(contract)


@router.post(
    "/{contract_id}/terminate",
    response_model=ContractResponse,
    summary="Terminate a contract",
)
@transactional()
async def terminate_contract(
    request: Request,
    body: ContractTerminateRequest,
    current_user: TokenData = Depends(get_current_user),
    contract: ContractEntity = Depends(get_contract_for_current_tenant),
    contract_repo: ContractRepository = Depends(get_contract_repository),
    audit_handler=Depends(get_audit_event_handler),
    db: AsyncSession = Depends(get_db),
):
    """Terminate a contract."""
    use_case = TransitionUseCase(contract_repo, "Contract")
    contract = await use_case.execute(
        contract.id,
        ContractTransition.TERMINATE,
        reason=body.reason,
        tenant_id=current_user.tenant_id,
    )
    await audit_change(contract, audit_handler, current_user, request)
    return _to_contract_response(contract)


@router.post(
    "/{contract_id}/archive",
    response_model=ContractResponse,
    summary="Archive a contract",
)
@transactional()
async def archive_contract(
    request: Request,
    current_user: TokenData = Depends(get_current_user),
    contract: ContractEntity = Depends(get_contract_for_current_tenant),
    contract_repo: ContractRepository = Depends(get_contract_repository),
    audit_handler=Depends(get_audit_event_handler),
    db: AsyncSession = Depends(get_db),
):
    """Archive a contract."""
    use_case = TransitionUseCase(contract_repo, "Contract")
    contract = await use_case.execute(
        contract.id, ContractTransition.ARCHIVE, tenant_id=current_user.tenant_id
    )
    await audit_change(contract, audit_handler, current_user, request)
    return _to_contract_response(contract)


@router.post(
    "/{contract_id}/restore",
    response_model=ContractResponse,
    summary="Restore a contract",
)
@transactional()
async def restore_contract(
    request: Request,
    current_user: TokenData = Depends(get_current_user),
    contract: ContractEntity = Depends(get_contract_for_current_tenant),
    contract_repo: ContractRepository = Depends(get_contract_repository),
    audit_handler=Depends(get_audit_event_handler),
    db: AsyncSession = Depends(get_db),
):
    """Restore a terminated or expired contract."""
    use_case = TransitionUseCase(contract_repo, "Contract")
    contract = await use_case.execute(
        contract.id, ContractTransition.RESTORE, tenant_id=current_user.tenant_id
    )
    await audit_change(contract, audit_handler, current_user, request)
    return _to_contract_response(contract)


@router.patch(
    "/{contract_id}",
    response_model=ContractResponse,
    summary="Update contract information",
)
@transactional()
async def update_contract(
    data: ContractUpdate,
    request: Request,
    current_user: TokenData = Depends(get_current_user),
    contract: ContractEntity = Depends(get_contract_for_current_tenant),
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
        contract.id,
        billing_rate=billing_rate,
        payment_frequency=data.payment_frequency,
        is_auto_renew=data.is_auto_renew,
    )
    await audit_change(contract, audit_handler, current_user, request)
    return _to_contract_response(contract)


@router.patch(
    "/{contract_id}/payment-status",
    response_model=ContractResponse,
    summary="Update contract payment status",
)
@transactional()
async def update_contract_payment_status(
    request: Request,
    body: ContractUpdatePaymentStatus,
    current_user: TokenData = Depends(get_current_user),
    contract: ContractEntity = Depends(get_contract_for_current_tenant),
    contract_repo: ContractRepository = Depends(get_contract_repository),
    audit_handler=Depends(get_audit_event_handler),
    db: AsyncSession = Depends(get_db),
):
    """Update contract payment status."""
    use_case = TransitionUseCase(contract_repo, "Contract")
    contract = await use_case.execute(
        contract.id,
        ContractTransition.UPDATE_PAYMENT_STATUS,
        payment_status=body.payment_status,
        tenant_id=current_user.tenant_id,
    )
    await audit_change(contract, audit_handler, current_user, request)
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
    current_user: TokenData = Depends(require_same_tenant),
    client_id: str | None = Query(None, description="Filter by client identifier"),
    status: ContractStatus | None = Query(None, description="Filter by contract status"),
    payment_status: PaymentStatus | None = Query(None, description="Filter by payment status"),
    is_auto_renew: bool | None = Query(
        None, description="Filter by whether the contract auto-renews"
    ),
    ends_from: date | None = Query(
        None,
        description="Only contracts whose term ends on or after this day (YYYY-MM-DD)",
    ),
    ends_to: date | None = Query(
        None,
        description="Only contracts whose term ends on or before this day (YYYY-MM-DD)",
    ),
    pg: PageParams = Depends(pagination()),
    sort_by: str = Query("created_at", description="Field to sort by"),
    sort_desc: bool = Query(True, description="Sort in descending order"),
    contract_repo: ContractRepository = Depends(get_contract_repository),
    db: AsyncSession = Depends(get_db),
):
    """
    List contracts with filtering, searching, and pagination.

    `ends_from`/`ends_to` window the end of the contract term; combined with
    `is_auto_renew` they express a renewal window ("auto-renewing contracts whose
    term ends in the next 30 days") without the server needing to know what
    "30 days" means to the caller.
    """

    contracts = await contract_repo.list_all(
        tenant_id=TenantId(tenant_id),
        client_id=ClientId(client_id) if client_id else None,
        status=status,
        payment_status=payment_status,
        is_auto_renew=is_auto_renew,
        ends_from=ends_from,
        ends_to=ends_to,
        limit=pg.limit,
        offset=pg.offset,
        sort_by=sort_by,
        sort_desc=sort_desc,
    )

    total = await contract_repo.count(
        tenant_id=TenantId(tenant_id),
        client_id=ClientId(client_id) if client_id else None,
        status=status,
        payment_status=payment_status,
        is_auto_renew=is_auto_renew,
        ends_from=ends_from,
        ends_to=ends_to,
    )

    return ContractListResponse(
        items=[_to_contract_response(contract) for contract in contracts],
        total=total,
        page=pg.page,
        limit=pg.limit,
        has_more=(pg.offset + pg.limit) < total,
    )


@router.get(
    "/{contract_id}",
    response_model=ContractResponse,
    summary="Get contract by ID",
)
@readonly()
async def get_contract(
    contract: ContractEntity = Depends(get_contract_for_current_tenant),
    db: AsyncSession = Depends(get_db),
):
    """Get contract by ID."""
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
    current_user: TokenData = Depends(require_same_tenant),
    contract_repo: ContractRepository = Depends(get_contract_repository),
    db: AsyncSession = Depends(get_db),
):
    """Get all contracts for a client."""
    contracts = await GetContractUseCase(contract_repo).execute_by_client(
        TenantId(tenant_id), ClientId(client_id)
    )
    return [_to_contract_response(contract) for contract in contracts]


@router.get(
    "/client/{client_id}/metrics",
    response_model=ContractMetricsResponse,
    summary="Coverage and session spend for each of a client's contract terms",
)
@readonly()
async def get_contract_metrics(
    client_id: str,
    tenant_id: str = Query(..., description="Tenant identifier"),
    current_user: TokenData = Depends(require_same_tenant),
    db: AsyncSession = Depends(get_db),
):
    """Count the services a term covers and sum what its sessions have cost.

    A session carries no contract, only a client and a date, so it is
    attributed to the term its date falls inside. Terms that overlap therefore
    both count the same session. Only completed sessions count, and a session
    with no rate adds nothing, which is why the priced count is reported
    alongside the total: 208 of the 369 sessions loaded into dev carry one, so
    a bare total would read as the whole cost when it is not.

    The date is taken in UTC before truncating, as `date_trunc` on a
    timestamptz otherwise buckets by the connection's timezone.
    """
    session_day = cast(func.timezone("UTC", ServiceSessionModel.scheduled_at), Date)
    services = (
        select(func.count(ServiceAssignmentModel.id))
        .where(
            ServiceAssignmentModel.contract_id == ContractModel.id,
            ServiceAssignmentModel.deleted_at.is_(None),
        )
        .correlate(ContractModel)
        .scalar_subquery()
    )
    rows = await db.execute(
        select(
            ContractModel.id,
            services,
            func.count(ServiceSessionModel.id),
            func.count(ServiceSessionModel.rate_ugx),
            func.coalesce(func.sum(ServiceSessionModel.rate_ugx), 0),
        )
        .select_from(ContractModel)
        .outerjoin(
            ServiceSessionModel,
            and_(
                ServiceSessionModel.tenant_id == ContractModel.tenant_id,
                ServiceSessionModel.client_id == ContractModel.client_id,
                ServiceSessionModel.deleted_at.is_(None),
                ServiceSessionModel.status == SessionStatus.COMPLETED,
                session_day.between(ContractModel.start_date, ContractModel.end_date),
            ),
        )
        .where(
            ContractModel.tenant_id == tenant_id,
            ContractModel.client_id == client_id,
            ContractModel.deleted_at.is_(None),
        )
        .group_by(ContractModel.id)
    )
    return ContractMetricsResponse(
        client_id=client_id,
        items=[
            ContractMetricsItem(
                contract_id=contract_id,
                services=int(services_count),
                sessions=int(sessions),
                sessions_priced=int(priced),
                spent=MoneySchema(amount=str(int(total)), currency=SESSION_RATE_CURRENCY),
            )
            for contract_id, services_count, sessions, priced, total in rows
        ],
    )


@router.get(
    "/client/{client_id}/active",
    response_model=ContractResponse,
    summary="Get active contract for a client",
)
@readonly()
async def get_active_contract_by_client(
    client_id: str,
    tenant_id: str = Query(..., description="Tenant identifier"),
    current_user: TokenData = Depends(require_same_tenant),
    contract_repo: ContractRepository = Depends(get_contract_repository),
    db: AsyncSession = Depends(get_db),
):
    """Get active contract for a client."""
    contract = await GetContractUseCase(contract_repo).execute_active_by_client(
        TenantId(tenant_id), ClientId(client_id)
    )
    if not contract:
        raise HTTPException(
            status_code=404,
            detail="Active contract not found for this client",
        )
    return _to_contract_response(contract)
