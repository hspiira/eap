"""Cross-tenant benchmark + consent routes (Phase 4 #D-Benchmark)."""

from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import (
    get_audit_event_handler,
    get_benchmark_collector,
    get_benchmark_consent_repository,
)
from app.api.schemas.benchmark_schemas import (
    BenchmarkConsentResponse,
    BenchmarkResultResponse,
    GrantConsentRequest,
    WithdrawConsentRequest,
)
from app.application.use_cases.benchmark_use_cases import (
    GetCrossTenantBenchmarkUseCase,
    GrantBenchmarkConsentUseCase,
    WithdrawBenchmarkConsentUseCase,
)
from app.core.authorization import require_same_tenant
from app.core.database import get_db
from app.core.security import TokenData, get_current_user
from app.domain.entities.benchmark_consent import BenchmarkConsent
from app.domain.enums import BenchmarkScope
from app.domain.repositories.benchmark_consent_repository import (
    BenchmarkConsentRepository,
)
from app.domain.value_objects.core import (
    BenchmarkConsentId,
    TenantId,
    UserId,
)
from app.shared.decorators import readonly, transactional
from app.shared.utils.generators import generate_cuid
from app.shared.utils.route_audit_helper import audit_change

router = APIRouter(prefix="/benchmark", tags=["benchmark"])


def _to_consent_response(c: BenchmarkConsent) -> BenchmarkConsentResponse:
    return BenchmarkConsentResponse(
        id=c.id.value,
        tenant_id=c.tenant_id.value,
        scope=c.scope,
        status=c.status,
        version=c.version,
        granted_by=c.granted_by.value,
        granted_at=c.granted_at,
        withdrawn_at=c.withdrawn_at,
        withdrawn_by=c.withdrawn_by.value if c.withdrawn_by else None,
        withdrawn_reason=c.withdrawn_reason,
        created_at=c.created_at,
        updated_at=c.updated_at,
    )


@router.post(
    "/consents",
    response_model=BenchmarkConsentResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Grant cross-tenant benchmark consent for a scope",
)
@transactional()
async def grant_consent(
    data: GrantConsentRequest,
    request: Request,
    current_user: TokenData = Depends(get_current_user),
    repo: BenchmarkConsentRepository = Depends(
        get_benchmark_consent_repository
    ),
    audit_handler=Depends(get_audit_event_handler),
    db: AsyncSession = Depends(get_db),
):
    consent = await GrantBenchmarkConsentUseCase(repo).execute(
        consent_id=BenchmarkConsentId(generate_cuid()),
        tenant_id=TenantId(current_user.tenant_id),
        scope=data.scope,
        version=data.version,
        granted_by=UserId(current_user.user_id),
    )
    await audit_change(consent, audit_handler, current_user, request)
    return _to_consent_response(consent)


@router.post(
    "/consents/{consent_id}/withdraw",
    response_model=BenchmarkConsentResponse,
    summary="Withdraw an active consent",
)
@transactional()
async def withdraw_consent(
    consent_id: str,
    data: WithdrawConsentRequest,
    request: Request,
    current_user: TokenData = Depends(get_current_user),
    repo: BenchmarkConsentRepository = Depends(
        get_benchmark_consent_repository
    ),
    db: AsyncSession = Depends(get_db),
):
    out = await WithdrawBenchmarkConsentUseCase(repo).execute(
        consent_id=BenchmarkConsentId(consent_id),
        actor=UserId(current_user.user_id),
        reason=data.reason,
    )
    require_same_tenant(current_user, out.tenant_id.value)
    return _to_consent_response(out)


@router.get(
    "/consents",
    response_model=list[BenchmarkConsentResponse],
    summary="List the current tenant's consents",
)
@readonly()
async def list_consents(
    current_user: TokenData = Depends(get_current_user),
    repo: BenchmarkConsentRepository = Depends(
        get_benchmark_consent_repository
    ),
    db: AsyncSession = Depends(get_db),
):
    rows = await repo.list_for_tenant(TenantId(current_user.tenant_id))
    return [_to_consent_response(c) for c in rows]


@router.get(
    "/{scope}",
    response_model=BenchmarkResultResponse,
    summary="Cross-tenant aggregate (k-anonymity enforced)",
)
@readonly()
async def get_benchmark(
    scope: BenchmarkScope,
    metric_code: str = Query(
        default="default",
        description="Identifier echoed in the response for client-side bookkeeping",
    ),
    from_date: datetime | None = Query(default=None),
    to_date: datetime | None = Query(default=None),
    current_user: TokenData = Depends(get_current_user),
    consents: BenchmarkConsentRepository = Depends(
        get_benchmark_consent_repository
    ),
    collector=Depends(get_benchmark_collector),
    db: AsyncSession = Depends(get_db),
):
    # Caller must hold an active consent for the scope they are querying.
    own = await consents.find_active_for_tenant_scope(
        TenantId(current_user.tenant_id), scope
    )
    if own is None:
        raise HTTPException(
            status_code=403,
            detail=(
                f"Tenant has no active consent for scope {scope.value}; "
                "grant one before querying"
            ),
        )
    result = await GetCrossTenantBenchmarkUseCase(consents, collector).execute(
        scope=scope,
        metric_code=metric_code,
        from_date=from_date,
        to_date=to_date,
    )
    return BenchmarkResultResponse(
        metric_code=result.metric_code,
        contributor_count=result.contributor_count,
        floor=result.floor,
        suppressed=result.suppressed,
        suppression_reason=result.suppression_reason,
        value=result.value,
    )
