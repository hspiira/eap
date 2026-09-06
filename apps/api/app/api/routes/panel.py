"""Provider panel-management routes (Phase 4 #D-Provider / SAD §5.2.4)."""

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
from app.core.database import get_db
from app.core.security import TokenData, get_current_user
from app.domain.exceptions import DomainError, NotFoundError
from app.domain.repositories.non_compete_clause_repository import (
    NonCompeteClauseRepository,
)
from app.domain.repositories.provider_repository import ProviderRepository
from app.domain.value_objects.core import (
    ProviderId,
    TenantId,
)
from app.shared.decorators import readonly, transactional

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
    provider_repo: ProviderRepository = Depends(get_provider_repository),
    audit_handler=Depends(get_audit_event_handler),
    db: AsyncSession = Depends(get_db),
):
    updated, skipped, not_found, not_provider = [], [], [], []
    for provider_id in data.provider_ids:
        row = await provider_repo.get_by_id(ProviderId(provider_id))
        if row is None or row[0].tenant_id != current_user.tenant_id:
            not_found.append(provider_id)
            continue
        provider, _user = row
        profile = provider.provider_profile
        if not profile:
            not_provider.append(provider_id)
            continue
        if profile.get("panel_status") == data.new_status.value:
            skipped.append(provider_id)
            continue
        provider.provider_profile = {**profile, "panel_status": data.new_status.value}
        await db.flush()
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
    row = await provider_repo.get_by_id(ProviderId(provider_id))
    if row is None or row[0].tenant_id != current_user.tenant_id:
        raise NotFoundError(f"Provider not found: {provider_id}")
    provider, _user = row
    if not provider.provider_profile:
        raise DomainError("Provider has no panel profile")
    provider.provider_profile = {**provider.provider_profile, "tier": data.new_tier.value}
    await db.flush()
    return TierChangeResponse(
        provider_id=provider.id,
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
    client_id: str | None = Query(default=None, description="Optional client scope for the check"),
    current_user: TokenData = Depends(get_current_user),
    provider_repo: ProviderRepository = Depends(get_provider_repository),
    clause_repo: NonCompeteClauseRepository = Depends(get_non_compete_clause_repository),
    db: AsyncSession = Depends(get_db),
):
    row = await provider_repo.get_by_id(ProviderId(provider_id))
    if row is None or row[0].tenant_id != current_user.tenant_id:
        raise NotFoundError(f"Provider not found: {provider_id}")
    profile = row[0].provider_profile
    clauses = await clause_repo.list_for_provider(TenantId(current_user.tenant_id), ProviderId(provider_id))
    binding = [c for c in clauses if c.is_currently_binding()]
    panel_eligible = bool(profile and profile.get("panel_status") == "Active" and profile.get("accreditation_status") == "Accredited")
    out = {
        "provider_id": provider_id,
        "client_id": client_id,
        "panel_eligible": panel_eligible,
        "binding_non_compete_count": len(binding),
        "binding_non_compete_ids": [c.id.value for c in binding],
        "eligible": panel_eligible and not binding,
        "reasons": [] if panel_eligible else ["Provider is not panel eligible"],
    }
    return ProviderEligibilityResponse(**out)
