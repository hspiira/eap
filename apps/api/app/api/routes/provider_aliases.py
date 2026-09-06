"""Practitioner alias review and reconciliation (decision 5).

There is deliberately no endpoint that resolves an alias automatically. A
practitioner is named only by a person choosing, and that choice is recorded
with its actor.
"""

from fastapi import APIRouter, Depends, Query, Request, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import get_audit_event_handler
from app.api.dependencies.pagination import PageParams, pagination
from app.api.dependencies.provider_network import get_provider_alias_repository
from app.api.schemas.provider_network_schemas import (
    ProviderAliasListResponse,
    ProviderAliasRejectRequest,
    ProviderAliasResolveRequest,
    ProviderAliasResponse,
)
from app.core.authorization import require_same_tenant, require_tenant_role
from app.core.database import get_db
from app.core.security import TokenData
from app.domain.entities.provider_alias import ProviderAliasEntity
from app.domain.enums.provider_network import AliasResolutionState
from app.domain.enums.tenancy import TenantRole
from app.domain.exceptions import NotFoundError
from app.domain.repositories.provider_network_repository import ProviderAliasRepository
from app.domain.value_objects.core import ProviderId, TenantId, UserId
from app.domain.value_objects.provider_network import ProviderAliasId
from app.shared.decorators import readonly, transactional
from app.shared.utils.datetime import utc_now
from app.shared.utils.route_audit_helper import audit_change

router = APIRouter(prefix="/provider-aliases", tags=["provider-aliases"])


def _response(alias: ProviderAliasEntity) -> ProviderAliasResponse:
    return ProviderAliasResponse(
        id=alias.id.value,
        tenant_id=alias.tenant_id.value,
        source_system=alias.source_system,
        source_value=alias.source_value,
        normalized_value=alias.normalized_value,
        state=alias.state,
        provider_id=alias.provider_id.value if alias.provider_id else None,
        candidate_provider_ids=list(alias.candidate_provider_ids),
        review_note=alias.review_note,
        created_at=alias.created_at,
        updated_at=alias.updated_at,
    )


async def _require(
    repo: ProviderAliasRepository, tenant_id: str, alias_id: str
) -> ProviderAliasEntity:
    alias = await repo.get_alias(TenantId(tenant_id), ProviderAliasId(alias_id))
    if alias is None:
        raise NotFoundError(
            "Provider alias not found", resource_type="ProviderAlias", resource_id=alias_id
        )
    return alias


@router.get("", response_model=ProviderAliasListResponse)
@readonly()
async def list_aliases(
    tenant_id: str = Query(...),
    source_system: str | None = Query(None),
    state: AliasResolutionState | None = Query(
        None, description="Filter the review queue by outcome"
    ),
    pg: PageParams = Depends(pagination()),
    current_user: TokenData = Depends(require_same_tenant),
    repo: ProviderAliasRepository = Depends(get_provider_alias_repository),
):
    items, total = await repo.list_aliases(
        TenantId(tenant_id),
        source_system=source_system,
        state=state.value if state else None,
        limit=pg.limit,
        offset=pg.offset,
    )
    return ProviderAliasListResponse(
        items=[_response(a) for a in items],
        total=total,
        page=pg.page,
        limit=pg.limit,
        has_more=(pg.offset + len(items)) < total,
    )


@router.post(
    "/{alias_id}/resolve",
    response_model=ProviderAliasResponse,
    status_code=status.HTTP_200_OK,
    dependencies=[Depends(require_tenant_role(TenantRole.ADMIN))],
)
@transactional()
async def resolve_alias(
    alias_id: str,
    data: ProviderAliasResolveRequest,
    request: Request,
    tenant_id: str = Query(...),
    current_user: TokenData = Depends(require_same_tenant),
    repo: ProviderAliasRepository = Depends(get_provider_alias_repository),
    audit_handler=Depends(get_audit_event_handler),
    db: AsyncSession = Depends(get_db),
):
    """Record that this source name is this practitioner.

    Admin-only, because a wrong mapping silently reattributes historical work.
    """
    alias = await _require(repo, tenant_id, alias_id)
    alias.resolve(ProviderId(data.provider_id), UserId(current_user.user_id), at=utc_now())
    await repo.save_alias(alias)
    await audit_change(alias, audit_handler, current_user, request)
    return _response(alias)


@router.post(
    "/{alias_id}/reject",
    response_model=ProviderAliasResponse,
    dependencies=[Depends(require_tenant_role(TenantRole.ADMIN))],
)
@transactional()
async def reject_alias(
    alias_id: str,
    data: ProviderAliasRejectRequest,
    request: Request,
    tenant_id: str = Query(...),
    current_user: TokenData = Depends(require_same_tenant),
    repo: ProviderAliasRepository = Depends(get_provider_alias_repository),
    audit_handler=Depends(get_audit_event_handler),
    db: AsyncSession = Depends(get_db),
):
    """Record that this source value does not name a practitioner."""
    alias = await _require(repo, tenant_id, alias_id)
    alias.reject(UserId(current_user.user_id), data.note, at=utc_now())
    await repo.save_alias(alias)
    await audit_change(alias, audit_handler, current_user, request)
    return _response(alias)
