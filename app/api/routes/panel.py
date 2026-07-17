"""Provider panel-management routes (Phase 4 #D-Provider / SAD §5.2.4)."""

from fastapi import APIRouter, Depends, Query, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import (
    get_audit_event_handler,
    get_non_compete_clause_repository,
    get_person_repository,
)
from app.api.schemas.panel_schemas import (
    BulkPanelStatusResponse,
    BulkPanelStatusUpdate,
    ProviderEligibilityResponse,
    TierChangeRequest,
    TierChangeResponse,
)
from app.application.use_cases.panel_use_cases import (
    BulkUpdatePanelStatusUseCase,
    ChangeProviderTierUseCase,
    CheckProviderEligibilityUseCase,
)
from app.core.database import get_db
from app.core.security import TokenData, get_current_user
from app.domain.repositories.non_compete_clause_repository import (
    NonCompeteClauseRepository,
)
from app.domain.repositories.person_repository import PersonRepository
from app.domain.value_objects.core import (
    ClientId,
    PersonId,
    TenantId,
    UserId,
)
from app.shared.decorators import readonly, transactional
from app.shared.utils.route_audit_helper import audit_change

router = APIRouter(prefix="/panel", tags=["panel"])


@router.patch(
    "/bulk-panel-status",
    response_model=BulkPanelStatusResponse,
    summary="Bulk update panel status (audit-trailed; supports the 80→8 cull)",
)
@transactional()
async def bulk_update_panel_status(
    data: BulkPanelStatusUpdate,
    request: Request,
    current_user: TokenData = Depends(get_current_user),
    person_repo: PersonRepository = Depends(get_person_repository),
    audit_handler=Depends(get_audit_event_handler),
    db: AsyncSession = Depends(get_db),
):
    use_case = BulkUpdatePanelStatusUseCase(person_repo)
    result = await use_case.execute(
        tenant_id=TenantId(current_user.tenant_id),
        provider_ids=[PersonId(p) for p in data.provider_ids],
        new_status=data.new_status,
        actor=UserId(current_user.user_id),
        reason=data.reason,
    )
    return BulkPanelStatusResponse(
        updated=result.updated,
        skipped_no_change=result.skipped_no_change,
        not_found=result.not_found,
        not_provider=result.not_provider,
        updated_count=len(result.updated),
        requested_count=len(data.provider_ids),
    )


@router.patch(
    "/{provider_id}/tier",
    response_model=TierChangeResponse,
    summary="Audited tier change for a provider",
)
@transactional()
async def change_provider_tier(
    provider_id: str,
    data: TierChangeRequest,
    request: Request,
    current_user: TokenData = Depends(get_current_user),
    person_repo: PersonRepository = Depends(get_person_repository),
    audit_handler=Depends(get_audit_event_handler),
    db: AsyncSession = Depends(get_db),
):
    person = await ChangeProviderTierUseCase(person_repo).execute(
        tenant_id=TenantId(current_user.tenant_id),
        provider_id=PersonId(provider_id),
        new_tier=data.new_tier,
        actor=UserId(current_user.user_id),
        reason=data.reason,
    )
    await audit_change(person, audit_handler, current_user, request)
    return TierChangeResponse(
        provider_id=person.id.value,
        new_tier=data.new_tier,
    )


@router.get(
    "/{provider_id}/eligibility",
    response_model=ProviderEligibilityResponse,
    summary="Pre-assignment eligibility check (panel + non-compete)",
)
@readonly()
async def check_provider_eligibility(
    provider_id: str,
    client_id: str | None = Query(
        default=None, description="Optional client scope for the check"
    ),
    current_user: TokenData = Depends(get_current_user),
    person_repo: PersonRepository = Depends(get_person_repository),
    clause_repo: NonCompeteClauseRepository = Depends(
        get_non_compete_clause_repository
    ),
    db: AsyncSession = Depends(get_db),
):
    use_case = CheckProviderEligibilityUseCase(person_repo, clause_repo)
    out = await use_case.execute(
        tenant_id=TenantId(current_user.tenant_id),
        provider_id=PersonId(provider_id),
        client_id=ClientId(client_id) if client_id else None,
    )
    return ProviderEligibilityResponse(**out)
