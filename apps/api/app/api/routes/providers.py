"""Independent provider/practitioner API."""

from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import get_audit_event_handler, get_provider_repository
from app.api.schemas.provider_schemas import (
    ProviderCreate,
    ProviderListResponse,
    ProviderResponse,
    ProviderUpdate,
)
from app.core.authorization import require_not_viewer, require_same_tenant
from app.core.database import get_db
from app.core.security import TokenData, get_current_user
from app.domain.entities.provider import ProviderEntity
from app.domain.entities.user import UserEntity
from app.domain.enums import BaseStatus
from app.domain.repositories.provider_repository import ProviderRepository
from app.domain.value_objects.core import ProviderId, ProviderProfile, TenantId, UserId
from app.shared.decorators import readonly, transactional
from app.shared.utils.datetime import utc_now
from app.shared.utils.generators import generate_cuid
from app.shared.utils.route_audit_helper import audit_change

router = APIRouter(prefix="/providers", tags=["providers"])


def _response(provider: ProviderEntity, user: UserEntity) -> ProviderResponse:
    if provider.provider_profile is None:
        raise HTTPException(status_code=409, detail="Provider profile is incomplete")
    return ProviderResponse(
        id=provider.id.value,
        tenant_id=provider.tenant_id.value,
        user_id=provider.user_id.value,
        display_name=user.display_name,
        email=user.email.value,
        status=provider.status,
        license_info=provider.license_info,
        provider_profile=provider.provider_profile,
        created_at=provider.created_at,
        updated_at=provider.updated_at,
    )


@router.get("", response_model=ProviderListResponse, summary="List independent providers")
@readonly()
async def list_providers(
    tenant_id: str = Query(...),
    limit: int = Query(100, ge=1, le=200),
    offset: int = Query(0, ge=0),
    current_user: TokenData = Depends(require_same_tenant),
    repo: ProviderRepository = Depends(get_provider_repository),
    db: AsyncSession = Depends(get_db),
):
    scope = TenantId(tenant_id)
    providers = await repo.list_for_tenant(scope, limit=limit, offset=offset)
    users = await repo.get_users_in_tenant([provider.user_id for provider in providers], scope)
    total = await repo.count(scope)
    return {
        "items": [
            _response(provider, users[provider.user_id.value])
            for provider in providers
            if provider.user_id.value in users
        ],
        "total": total,
        "has_more": offset + len(providers) < total,
    }


@router.get("/{provider_id}", response_model=ProviderResponse)
@readonly()
async def get_provider(
    provider_id: str,
    current_user: TokenData = Depends(get_current_user),
    repo: ProviderRepository = Depends(get_provider_repository),
    db: AsyncSession = Depends(get_db),
):
    provider = await repo.get_by_id(ProviderId(provider_id))
    if provider is None or provider.tenant_id.value != current_user.tenant_id:
        raise HTTPException(status_code=404, detail="Provider not found")
    user = await repo.get_user_in_tenant(provider.user_id, provider.tenant_id)
    if user is None:
        raise HTTPException(status_code=409, detail="Provider account is unavailable")
    return _response(provider, user)


@router.post(
    "",
    response_model=ProviderResponse,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_not_viewer)],
)
@transactional()
async def create_provider(
    data: ProviderCreate,
    request: Request,
    tenant_id: str = Query(...),
    current_user: TokenData = Depends(require_same_tenant),
    repo: ProviderRepository = Depends(get_provider_repository),
    audit_handler=Depends(get_audit_event_handler),
    db: AsyncSession = Depends(get_db),
):
    scope = TenantId(tenant_id)
    user = await repo.get_user_in_tenant(UserId(data.user_id), scope)
    if user is None:
        raise HTTPException(status_code=404, detail="User not found in tenant")
    now = utc_now()
    provider = ProviderEntity(
        id=ProviderId(generate_cuid()),
        tenant_id=scope,
        user_id=user.id,
        status=BaseStatus.PENDING,
        provider_profile=ProviderProfile(**data.provider_profile.model_dump()),
        license_info=data.license_info,
        created_at=now,
        updated_at=now,
    )
    await repo.save(provider)
    await audit_change(provider, audit_handler, current_user, request)
    return _response(provider, user)


@router.patch(
    "/{provider_id}", response_model=ProviderResponse, dependencies=[Depends(require_not_viewer)]
)
@transactional()
async def update_provider(
    provider_id: str,
    data: ProviderUpdate,
    request: Request,
    current_user: TokenData = Depends(get_current_user),
    repo: ProviderRepository = Depends(get_provider_repository),
    audit_handler=Depends(get_audit_event_handler),
    db: AsyncSession = Depends(get_db),
):
    provider = await repo.get_by_id(ProviderId(provider_id))
    if provider is None or provider.tenant_id.value != current_user.tenant_id:
        raise HTTPException(status_code=404, detail="Provider not found")
    user = await repo.get_user_in_tenant(provider.user_id, provider.tenant_id)
    if user is None:
        raise HTTPException(status_code=409, detail="Provider account is unavailable")
    if data.provider_profile is not None:
        provider.replace_profile(ProviderProfile(**data.provider_profile.model_dump()))
    if data.license_info is not None:
        provider.license_info = data.license_info
    if data.status is not None:
        provider.status = data.status
    provider.updated_at = utc_now()
    await repo.save(provider)
    await audit_change(provider, audit_handler, current_user, request)
    return _response(provider, user)
