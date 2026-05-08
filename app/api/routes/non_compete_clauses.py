"""Non-compete clause routes (Phase 2 #D-Provider)."""

from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import (
    get_audit_event_handler,
    get_non_compete_clause_repository,
)
from app.api.schemas.non_compete_schemas import (
    NonCompeteCreate,
    NonCompeteResponse,
    NonCompeteRevoke,
    NonCompeteSign,
)
from app.application.use_cases.transitions import (
    NonCompeteTransition,
    TransitionUseCase,
)
from app.core.authorization import require_same_tenant
from app.core.database import get_db
from app.core.security import TokenData, get_current_user
from app.domain.entities.non_compete_clause import NonCompeteClauseEntity
from app.domain.enums import NonCompeteStatus
from app.domain.repositories.non_compete_clause_repository import (
    NonCompeteClauseRepository,
)
from app.domain.value_objects.core import (
    NonCompeteClauseId,
    PersonId,
    TenantId,
    UserId,
)
from app.shared.decorators import readonly, transactional
from app.shared.utils.datetime import utc_now
from app.shared.utils.generators import generate_cuid
from app.shared.utils.route_audit_helper import audit_entity_operation

router = APIRouter(prefix="/non-compete-clauses", tags=["non-compete"])


def _to_response(clause: NonCompeteClauseEntity) -> NonCompeteResponse:
    return NonCompeteResponse(
        id=clause.id.value,
        tenant_id=clause.tenant_id.value,
        provider_id=clause.provider_id.value,
        status=clause.status,
        terms_summary=clause.terms_summary,
        effective_from=clause.effective_from,
        effective_until=clause.effective_until,
        signed_at=clause.signed_at,
        signed_by=clause.signed_by.value if clause.signed_by else None,
        revoked_at=clause.revoked_at,
        revoked_reason=clause.revoked_reason,
        document_id=clause.document_id,
        created_at=clause.created_at,
        updated_at=clause.updated_at,
    )


@router.post(
    "",
    response_model=NonCompeteResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Draft a new non-compete clause",
)
@transactional()
async def create_non_compete(
    data: NonCompeteCreate,
    request: Request,
    tenant_id: str = Query(..., description="Tenant identifier"),
    current_user: TokenData = Depends(require_same_tenant),
    repo: NonCompeteClauseRepository = Depends(get_non_compete_clause_repository),
    audit_handler=Depends(get_audit_event_handler),
    db: AsyncSession = Depends(get_db),
):
    now = utc_now()
    clause = NonCompeteClauseEntity(
        id=NonCompeteClauseId(generate_cuid()),
        tenant_id=TenantId(tenant_id),
        provider_id=PersonId(data.provider_id),
        status=NonCompeteStatus.DRAFT,
        terms_summary=data.terms_summary,
        effective_from=data.effective_from,
        effective_until=data.effective_until,
        document_id=data.document_id,
        created_at=now,
        updated_at=now,
    )
    await repo.save(clause)
    await audit_entity_operation(
        entity=clause,
        audit_handler=audit_handler,
        tenant_id=clause.tenant_id,
        user_id=current_user.user_id,
        request=request,
    )
    return _to_response(clause)


@router.post(
    "/{clause_id}/sign",
    response_model=NonCompeteResponse,
    summary="Sign a draft non-compete clause",
)
@transactional()
async def sign_non_compete(
    clause_id: str,
    body: NonCompeteSign,
    request: Request,
    current_user: TokenData = Depends(get_current_user),
    repo: NonCompeteClauseRepository = Depends(get_non_compete_clause_repository),
    audit_handler=Depends(get_audit_event_handler),
    db: AsyncSession = Depends(get_db),
):
    use_case: TransitionUseCase = TransitionUseCase(repo)
    use_case.entity_name = "NonCompeteClause"
    clause = await use_case.execute(
        NonCompeteClauseId(clause_id),
        NonCompeteTransition.SIGN,
        signed_by=UserId(body.signed_by),
    )
    await audit_entity_operation(
        entity=clause,
        audit_handler=audit_handler,
        tenant_id=clause.tenant_id,
        user_id=current_user.user_id,
        request=request,
    )
    return _to_response(clause)


@router.post(
    "/{clause_id}/revoke",
    response_model=NonCompeteResponse,
    summary="Revoke a non-compete clause",
)
@transactional()
async def revoke_non_compete(
    clause_id: str,
    body: NonCompeteRevoke,
    request: Request,
    current_user: TokenData = Depends(get_current_user),
    repo: NonCompeteClauseRepository = Depends(get_non_compete_clause_repository),
    audit_handler=Depends(get_audit_event_handler),
    db: AsyncSession = Depends(get_db),
):
    use_case: TransitionUseCase = TransitionUseCase(repo)
    use_case.entity_name = "NonCompeteClause"
    clause = await use_case.execute(
        NonCompeteClauseId(clause_id),
        NonCompeteTransition.REVOKE,
        reason=body.reason,
    )
    await audit_entity_operation(
        entity=clause,
        audit_handler=audit_handler,
        tenant_id=clause.tenant_id,
        user_id=current_user.user_id,
        request=request,
    )
    return _to_response(clause)


@router.get(
    "/{clause_id}",
    response_model=NonCompeteResponse,
    summary="Get a non-compete clause by ID",
)
@readonly()
async def get_non_compete(
    clause_id: str,
    _user: TokenData = Depends(get_current_user),
    repo: NonCompeteClauseRepository = Depends(get_non_compete_clause_repository),
    db: AsyncSession = Depends(get_db),
):
    clause = await repo.get_by_id(NonCompeteClauseId(clause_id))
    if clause is None:
        raise HTTPException(status_code=404, detail="Non-compete clause not found")
    return _to_response(clause)


@router.get(
    "/provider/{provider_id}",
    response_model=list[NonCompeteResponse],
    summary="List non-compete clauses for a provider",
)
@readonly()
async def list_for_provider(
    provider_id: str,
    tenant_id: str = Query(..., description="Tenant identifier"),
    current_user: TokenData = Depends(require_same_tenant),
    repo: NonCompeteClauseRepository = Depends(get_non_compete_clause_repository),
    db: AsyncSession = Depends(get_db),
):
    clauses = await repo.list_for_provider(
        TenantId(tenant_id), PersonId(provider_id)
    )
    return [_to_response(c) for c in clauses]
