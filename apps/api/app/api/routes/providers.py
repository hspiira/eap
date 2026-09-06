"""Independent provider/practitioner API."""

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import get_provider_repository
from app.api.schemas.provider_schemas import (
    ProviderCreate,
    ProviderListResponse,
    ProviderResponse,
    ProviderUpdate,
)
from app.core.authorization import require_not_viewer, require_same_tenant
from app.core.database import get_db
from app.core.security import TokenData, get_current_user
from app.domain.repositories.provider_repository import ProviderRepository
from app.domain.value_objects.core import ProviderId, TenantId
from app.shared.decorators import readonly, transactional

router = APIRouter(prefix="/providers", tags=["providers"])


def _response(row) -> ProviderResponse:
    provider, user = row
    if provider.provider_profile is None:
        raise HTTPException(status_code=409, detail="Provider profile is incomplete")
    return ProviderResponse(
        id=provider.id,
        tenant_id=provider.tenant_id,
        user_id=provider.user_id,
        display_name=user.display_name,
        email=user.email,
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
    rows = await repo.list_for_tenant(TenantId(tenant_id), limit=limit, offset=offset)
    total = await repo.count(TenantId(tenant_id))
    return {
        "items": [_response(row) for row in rows],
        "total": total,
        "has_more": offset + len(rows) < total,
    }


@router.get("/{provider_id}", response_model=ProviderResponse)
@readonly()
async def get_provider(
    provider_id: str,
    current_user: TokenData = Depends(get_current_user),
    repo: ProviderRepository = Depends(get_provider_repository),
    db: AsyncSession = Depends(get_db),
):
    row = await repo.get_by_id(ProviderId(provider_id))
    if row is None or row[0].tenant_id != current_user.tenant_id:
        raise HTTPException(status_code=404, detail="Provider not found")
    return _response(row)


@router.post(
    "",
    response_model=ProviderResponse,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_not_viewer)],
)
@transactional()
async def create_provider(
    data: ProviderCreate,
    tenant_id: str = Query(...),
    current_user: TokenData = Depends(require_same_tenant),
    repo: ProviderRepository = Depends(get_provider_repository),
    db: AsyncSession = Depends(get_db),
):
    user = await repo.get_user_in_tenant(data.user_id, TenantId(tenant_id))
    if user is None:
        raise HTTPException(status_code=404, detail="User not found in tenant")
    provider = await repo.create(
        tenant_id=TenantId(tenant_id),
        user_id=data.user_id,
        provider_profile=data.provider_profile.model_dump(mode="json"),
        license_info=data.license_info,
    )
    return _response((provider, user))


@router.patch(
    "/{provider_id}", response_model=ProviderResponse, dependencies=[Depends(require_not_viewer)]
)
@transactional()
async def update_provider(
    provider_id: str,
    data: ProviderUpdate,
    current_user: TokenData = Depends(get_current_user),
    repo: ProviderRepository = Depends(get_provider_repository),
    db: AsyncSession = Depends(get_db),
):
    row = await repo.get_by_id(ProviderId(provider_id))
    if row is None or row[0].tenant_id != current_user.tenant_id:
        raise HTTPException(status_code=404, detail="Provider not found")
    provider, user = row
    if data.provider_profile is not None:
        provider.provider_profile = data.provider_profile.model_dump(mode="json")
    if data.license_info is not None:
        provider.license_info = data.license_info
    if data.status is not None:
        provider.status = data.status
    await db.flush()
    return _response((provider, user))
