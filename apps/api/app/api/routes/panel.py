"""Provider panel-management routes.

Bulk panel moves and the eligibility preview. Both delegate to the same
aggregate commands and the same eligibility policy the write paths use, so the
panel API and the practitioner API cannot drift apart.
"""

from datetime import datetime

from fastapi import APIRouter, Depends, Query, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import (
    get_audit_event_handler,
    get_non_compete_clause_repository,
    get_provider_repository,
)
from app.api.schemas.panel_schemas import (
    BulkPanelStatusResponse,
    BulkPanelStatusUpdate,
    ProviderEligibilityResponse,
    TierChangeRequest,
    TierChangeResponse,
)
from app.core.authorization import require_tenant_role
from app.core.database import get_db
from app.core.security import TokenData, get_current_user
from app.domain.enums import TenantRole
from app.domain.exceptions import DomainError, NotFoundError
from app.domain.repositories.non_compete_clause_repository import (
    NonCompeteClauseRepository,
)
from app.domain.repositories.provider_repository import ProviderRepository
from app.domain.services.provider_eligibility import evaluate_practitioner
from app.domain.value_objects.core import (
    ProviderId,
    TenantId,
    UserId,
)
from app.shared.decorators import readonly, transactional
from app.shared.utils.datetime import ensure_utc, utc_now
from app.shared.utils.route_audit_helper import audit_change

router = APIRouter(prefix="/panel", tags=["panel"])

require_admin = require_tenant_role(TenantRole.ADMIN)


@router.patch(
    "/bulk-panel-status",
    response_model=BulkPanelStatusResponse,
    dependencies=[Depends(require_admin)],
    summary="Bulk update panel status (audit-trailed; supports the 80 to 8 cull)",
)
@transactional()
async def bulk_update_panel_status(
    data: BulkPanelStatusUpdate,
    request: Request,
    current_user: TokenData = Depends(get_current_user),
    provider_repo: ProviderRepository = Depends(get_provider_repository),
    audit_handler=Depends(get_audit_event_handler),
    db: AsyncSession = Depends(get_db),
):
    updated, skipped, not_found, not_provider = [], [], [], []
    actor = UserId(current_user.user_id)
    for provider_id in data.provider_ids:
        provider = await provider_repo.get_by_id(ProviderId(provider_id))
        if provider is None or provider.tenant_id.value != current_user.tenant_id:
            not_found.append(provider_id)
            continue
        profile = provider.provider_profile
        if not profile:
            not_provider.append(provider_id)
            continue
        if profile.panel_status == data.new_status:
            skipped.append(provider_id)
            continue
        provider.change_panel_status(data.new_status, actor, data.reason)
        await provider_repo.save(provider)
        await audit_change(provider, audit_handler, current_user, request)
        updated.append(provider_id)
    return BulkPanelStatusResponse(
        updated=updated,
        skipped_no_change=skipped,
        not_found=not_found,
        not_provider=not_provider,
        updated_count=len(updated),
        requested_count=len(data.provider_ids),
    )


@router.patch(
    "/{provider_id}/tier",
    response_model=TierChangeResponse,
    dependencies=[Depends(require_admin)],
    summary="Audited tier change for a provider",
)
@transactional()
async def change_provider_tier(
    provider_id: str,
    data: TierChangeRequest,
    request: Request,
    current_user: TokenData = Depends(get_current_user),
    provider_repo: ProviderRepository = Depends(get_provider_repository),
    audit_handler=Depends(get_audit_event_handler),
    db: AsyncSession = Depends(get_db),
):
    provider = await provider_repo.get_by_id(ProviderId(provider_id))
    if provider is None or provider.tenant_id.value != current_user.tenant_id:
        raise NotFoundError(f"Provider not found: {provider_id}")
    if not provider.provider_profile:
        raise DomainError("Provider has no panel profile")
    provider.change_tier(data.new_tier, UserId(current_user.user_id), data.reason)
    await provider_repo.save(provider)
    await audit_change(provider, audit_handler, current_user, request)
    return TierChangeResponse(
        provider_id=provider.id.value,
        new_tier=data.new_tier,
    )


@router.get(
    "/{provider_id}/eligibility",
    response_model=ProviderEligibilityResponse,
    summary="Pre-assignment eligibility preview; the write path re-evaluates it",
)
@readonly()
async def check_provider_eligibility(
    provider_id: str,
    client_id: str | None = Query(default=None, description="Optional client scope for the check"),
    scheduled_at: datetime | None = Query(
        default=None, description="Service date to check; defaults to now"
    ),
    current_user: TokenData = Depends(get_current_user),
    provider_repo: ProviderRepository = Depends(get_provider_repository),
    clause_repo: NonCompeteClauseRepository = Depends(get_non_compete_clause_repository),
    db: AsyncSession = Depends(get_db),
):
    provider = await provider_repo.get_by_id(ProviderId(provider_id))
    if provider is None or provider.tenant_id.value != current_user.tenant_id:
        raise NotFoundError(f"Provider not found: {provider_id}")
    now = utc_now()
    service_time = ensure_utc(scheduled_at) or now
    decision = evaluate_practitioner(provider, scheduled_at=service_time, now=now)
    clauses = await clause_repo.list_for_provider(
        TenantId(current_user.tenant_id), ProviderId(provider_id)
    )
    binding = [c for c in clauses if c.is_currently_binding()]
    return ProviderEligibilityResponse(
        provider_id=provider_id,
        client_id=client_id,
        scheduled_at=service_time,
        panel_eligible=decision.eligible,
        binding_non_compete_count=len(binding),
        binding_non_compete_ids=[c.id.value for c in binding],
        eligible=decision.eligible,
        reasons=[reason.message for reason in decision.reasons],
        failures=[{"code": reason.code, "message": reason.message} for reason in decision.reasons],
    )
