"""
Contract API Routes

FastAPI routes for Contract operations.
Follows hybrid approach: Commands use use cases, Queries use repositories directly.
"""

import decimal
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import get_contract_repository
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
from app.domain.enums import ContractStatus, PaymentFrequency, PaymentStatus
from app.domain.entities.contract import ContractEntity
from app.domain.exceptions import DomainError
from app.domain.repositories.contract_repository import ContractRepository
from app.domain.value_objects.core import (
    ClientId,
    ContractId,
    DateRange,
    Money,
    TenantId,
)
from app.shared.utils.generators import generate_cuid
from app.shared.utils.http_errors import get_error_status_code

router = APIRouter(prefix="/contracts", tags=["contracts"])


def _to_contract_response(contract: ContractEntity) -> ContractResponse:
    """Map ContractEntity to API response."""
    period = DateRangeSchema(
        start_date=contract._period.start_date,
        end_date=contract._period.end_date,
    )

    billing_rate = MoneySchema(
        amount=str(contract._billing_rate.amount),
        currency=contract._billing_rate.currency,
    )

    return ContractResponse(
        id=contract._id.value,
        tenant_id=contract._tenant_id.value,
        client_id=contract._client_id.value,
        period=period,
        billing_rate=billing_rate,
        payment_frequency=contract._payment_frequency,
        payment_status=contract._payment_status,
        status=contract._status,
        is_auto_renew=contract._is_auto_renew,
        last_billing_date=contract._last_billing_date,
        next_billing_date=contract._next_billing_date,
        signed_by=contract._signed_by,
        signed_at=contract._signed_at,
        termination_reason=contract._termination_reason,
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
async def create_contract(
    data: ContractCreate,
    tenant_id: str = Query(..., description="Tenant identifier"),
    contract_repo: ContractRepository = Depends(get_contract_repository),
    db: AsyncSession = Depends(get_db),
):
    """
    Create a new contract.

    This is a COMMAND operation, so it uses a use case for orchestration.
    """
    try:
        # Convert schemas to value objects
        billing_rate = Money(
            amount=decimal.Decimal(data.billing_rate.amount),
            currency=data.billing_rate.currency,
        )

        period = DateRange(start_date=data.start_date, end_date=data.end_date)

        create_use_case = CreateContractUseCase(contract_repo)

        contract = await create_use_case.execute(
            contract_id=ContractId(generate_cuid()),
            tenant_id=TenantId(tenant_id),
            client_id=ClientId(data.client_id),
            start_date=data.start_date,
            end_date=data.end_date,
            billing_rate=billing_rate,
            payment_frequency=data.payment_frequency,
            is_auto_renew=data.is_auto_renew,
        )

        await db.commit()

        return _to_contract_response(contract)
    except ValueError as e:
        await db.rollback()
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)) from e
    except DomainError as e:
        await db.rollback()
        status_code = get_error_status_code(str(e))
        raise HTTPException(status_code=status_code, detail=str(e)) from e


@router.post(
    "/{contract_id}/activate",
    response_model=ContractResponse,
    summary="Activate a contract",
)
async def activate_contract(
    contract_id: str,
    contract_repo: ContractRepository = Depends(get_contract_repository),
    db: AsyncSession = Depends(get_db),
):
    """
    Activate a contract.

    This is a COMMAND operation, so it uses a use case for orchestration.
    """
    try:
        activate_use_case = ActivateContractUseCase(contract_repo)

        contract = await activate_use_case.execute(ContractId(contract_id))

        await db.commit()

        return _to_contract_response(contract)
    except ValueError as e:
        await db.rollback()
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e)) from e
    except DomainError as e:
        await db.rollback()
        status_code = get_error_status_code(str(e))
        raise HTTPException(status_code=status_code, detail=str(e)) from e


@router.post(
    "/{contract_id}/sign",
    response_model=ContractResponse,
    summary="Sign a contract",
)
async def sign_contract(
    contract_id: str,
    request: ContractSignRequest,
    contract_repo: ContractRepository = Depends(get_contract_repository),
    db: AsyncSession = Depends(get_db),
):
    """
    Sign a contract.

    This is a COMMAND operation, so it uses a use case for orchestration.
    """
    try:
        sign_use_case = SignContractUseCase(contract_repo)

        contract = await sign_use_case.execute(
            ContractId(contract_id), request.signed_by
        )

        await db.commit()

        return _to_contract_response(contract)
    except ValueError as e:
        await db.rollback()
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e)) from e
    except DomainError as e:
        await db.rollback()
        status_code = get_error_status_code(str(e))
        raise HTTPException(status_code=status_code, detail=str(e)) from e


@router.post(
    "/{contract_id}/renew",
    response_model=ContractResponse,
    summary="Renew a contract",
)
async def renew_contract(
    contract_id: str,
    request: ContractRenewRequest,
    contract_repo: ContractRepository = Depends(get_contract_repository),
    db: AsyncSession = Depends(get_db),
):
    """
    Renew a contract.

    This is a COMMAND operation, so it uses a use case for orchestration.
    """
    try:
        new_rate = None
        if request.new_rate:
            new_rate = Money(
                amount=decimal.Decimal(request.new_rate.amount),
                currency=request.new_rate.currency,
            )

        renew_use_case = RenewContractUseCase(contract_repo)

        # Convert datetime to date for renew method
        new_end_date = request.new_end_date.date()

        contract = await renew_use_case.execute(
            ContractId(contract_id), new_end_date, new_rate
        )

        await db.commit()

        return _to_contract_response(contract)
    except ValueError as e:
        await db.rollback()
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e)) from e
    except DomainError as e:
        await db.rollback()
        status_code = get_error_status_code(str(e))
        raise HTTPException(status_code=status_code, detail=str(e)) from e


@router.post(
    "/{contract_id}/terminate",
    response_model=ContractResponse,
    summary="Terminate a contract",
)
async def terminate_contract(
    contract_id: str,
    request: ContractTerminateRequest,
    contract_repo: ContractRepository = Depends(get_contract_repository),
    db: AsyncSession = Depends(get_db),
):
    """
    Terminate a contract.

    This is a COMMAND operation, so it uses a use case for orchestration.
    """
    try:
        terminate_use_case = TerminateContractUseCase(contract_repo)

        contract = await terminate_use_case.execute(
            ContractId(contract_id), request.reason
        )

        await db.commit()

        return _to_contract_response(contract)
    except ValueError as e:
        await db.rollback()
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e)) from e
    except DomainError as e:
        await db.rollback()
        status_code = get_error_status_code(str(e))
        raise HTTPException(status_code=status_code, detail=str(e)) from e


@router.post(
    "/{contract_id}/archive",
    response_model=ContractResponse,
    summary="Archive a contract",
)
async def archive_contract(
    contract_id: str,
    contract_repo: ContractRepository = Depends(get_contract_repository),
    db: AsyncSession = Depends(get_db),
):
    """
    Archive a contract.

    This is a COMMAND operation, so it uses a use case for orchestration.
    """
    try:
        archive_use_case = ArchiveContractUseCase(contract_repo)

        contract = await archive_use_case.execute(ContractId(contract_id))

        await db.commit()

        return _to_contract_response(contract)
    except ValueError as e:
        await db.rollback()
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e)) from e
    except DomainError as e:
        await db.rollback()
        status_code = get_error_status_code(str(e))
        raise HTTPException(status_code=status_code, detail=str(e)) from e


@router.post(
    "/{contract_id}/restore",
    response_model=ContractResponse,
    summary="Restore a contract",
)
async def restore_contract(
    contract_id: str,
    contract_repo: ContractRepository = Depends(get_contract_repository),
    db: AsyncSession = Depends(get_db),
):
    """
    Restore a terminated or expired contract.

    This is a COMMAND operation, so it uses a use case for orchestration.
    """
    try:
        restore_use_case = RestoreContractUseCase(contract_repo)

        contract = await restore_use_case.execute(ContractId(contract_id))

        await db.commit()

        return _to_contract_response(contract)
    except ValueError as e:
        await db.rollback()
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e)) from e
    except DomainError as e:
        await db.rollback()
        status_code = get_error_status_code(str(e))
        raise HTTPException(status_code=status_code, detail=str(e)) from e


@router.patch(
    "/{contract_id}",
    response_model=ContractResponse,
    summary="Update contract information",
)
async def update_contract(
    contract_id: str,
    data: ContractUpdate,
    contract_repo: ContractRepository = Depends(get_contract_repository),
    db: AsyncSession = Depends(get_db),
):
    """
    Update contract information.

    This is a COMMAND operation, so it uses a use case for orchestration.
    """
    try:
        billing_rate = None
        if data.billing_rate:
            billing_rate = Money(
                amount=decimal.Decimal(data.billing_rate.amount),
                currency=data.billing_rate.currency,
            )

        update_use_case = UpdateContractUseCase(contract_repo)

        contract = await update_use_case.execute(
            ContractId(contract_id),
            billing_rate=billing_rate,
            payment_frequency=data.payment_frequency,
            is_auto_renew=data.is_auto_renew,
        )

        await db.commit()

        return _to_contract_response(contract)
    except ValueError as e:
        await db.rollback()
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e)) from e
    except DomainError as e:
        await db.rollback()
        status_code = get_error_status_code(str(e))
        raise HTTPException(status_code=status_code, detail=str(e)) from e


@router.patch(
    "/{contract_id}/payment-status",
    response_model=ContractResponse,
    summary="Update contract payment status",
)
async def update_contract_payment_status(
    contract_id: str,
    request: ContractUpdatePaymentStatus,
    contract_repo: ContractRepository = Depends(get_contract_repository),
    db: AsyncSession = Depends(get_db),
):
    """
    Update contract payment status.

    This is a COMMAND operation, so it uses a use case for orchestration.
    """
    try:
        update_use_case = UpdateContractPaymentStatusUseCase(contract_repo)

        contract = await update_use_case.execute(
            ContractId(contract_id), request.payment_status
        )

        await db.commit()

        return _to_contract_response(contract)
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
    response_model=ContractListResponse,
    summary="List contracts with filtering and pagination",
)
async def list_contracts(
    tenant_id: str = Query(..., description="Tenant identifier"),
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
):
    """
    List contracts with filtering, searching, and pagination.

    This is a QUERY operation, so it calls the repository directly.
    """
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

    contract_responses = [_to_contract_response(contract) for contract in contracts]

    return ContractListResponse(
        items=contract_responses,
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
async def get_contract(
    contract_id: str,
    contract_repo: ContractRepository = Depends(get_contract_repository),
):
    """
    Get contract by ID.

    This is a QUERY operation, so it calls the repository directly.
    """
    contract = await contract_repo.get_by_id(ContractId(contract_id))

    if not contract:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Contract not found"
        )

    return _to_contract_response(contract)


@router.get(
    "/client/{client_id}",
    response_model=list[ContractResponse],
    summary="Get all contracts for a client",
)
async def get_contracts_by_client(
    client_id: str,
    tenant_id: str = Query(..., description="Tenant identifier"),
    contract_repo: ContractRepository = Depends(get_contract_repository),
):
    """
    Get all contracts for a client.

    This is a QUERY operation, so it calls the repository directly.
    """
    get_use_case = GetContractUseCase(contract_repo)

    contracts = await get_use_case.execute_by_client(
        TenantId(tenant_id), ClientId(client_id)
    )

    return [_to_contract_response(contract) for contract in contracts]


@router.get(
    "/client/{client_id}/active",
    response_model=ContractResponse,
    summary="Get active contract for a client",
)
async def get_active_contract_by_client(
    client_id: str,
    tenant_id: str = Query(..., description="Tenant identifier"),
    contract_repo: ContractRepository = Depends(get_contract_repository),
):
    """
    Get active contract for a client.

    This is a QUERY operation, so it calls the repository directly.
    """
    get_use_case = GetContractUseCase(contract_repo)

    contract = await get_use_case.execute_active_by_client(
        TenantId(tenant_id), ClientId(client_id)
    )

    if not contract:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No active contract found for this client",
        )

    return _to_contract_response(contract)
