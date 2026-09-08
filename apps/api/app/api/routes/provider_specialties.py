"""Global specialty catalogue and tenant-owned practitioner links (decision 5).

Catalogue writes are platform-level, because a shared vocabulary that any
tenant can edit stops being comparable. Link writes are tenant-scoped.
"""

from fastapi import APIRouter, Depends, Query, Request, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import get_audit_event_handler
from app.api.dependencies.provider_network import get_provider_specialty_repository
from app.api.schemas.provider_network_schemas import (
    ProviderSpecialtyCreate,
    ProviderSpecialtyLinkCreate,
    ProviderSpecialtyLinkResponse,
    ProviderSpecialtyResponse,
)
from app.core.authorization import (
    require_not_viewer,
    require_platform_admin,
    require_same_tenant,
)
from app.core.database import get_db
from app.core.reference_cache import cached_lookup, invalidate_reference_cache
from app.core.security import TokenData
from app.domain.entities.provider_specialty import (
    ProviderSpecialtyEntity,
    ProviderSpecialtyLinkEntity,
)
from app.domain.exceptions import DomainError, NotFoundError
from app.domain.repositories.provider_network_repository import ProviderSpecialtyRepository
from app.domain.value_objects.core import ProviderId, TenantId, UserId
from app.domain.value_objects.provider_network import (
    ProviderSpecialtyId,
    ProviderSpecialtyLinkId,
)
from app.shared.decorators import readonly, transactional
from app.shared.utils.datetime import utc_now
from app.shared.utils.generators import generate_cuid
from app.shared.utils.route_audit_helper import audit_change

router = APIRouter(prefix="/provider-specialties", tags=["provider-specialties"])

_RESOURCE = "provider_specialties"


def _response(specialty: ProviderSpecialtyEntity) -> ProviderSpecialtyResponse:
    return ProviderSpecialtyResponse(
        id=specialty.id.value,
        code=specialty.code,
        label=specialty.label,
        is_active=specialty.is_active,
    )


@router.get("", response_model=list[ProviderSpecialtyResponse])
@readonly()
@cached_lookup(_RESOURCE)
async def list_specialties(
    include_inactive: bool = Query(False),
    repo: ProviderSpecialtyRepository = Depends(get_provider_specialty_repository),
):
    """Readable by any authenticated caller; the vocabulary carries no tenant."""
    return [_response(s) for s in await repo.list_specialties(include_inactive=include_inactive)]


@router.post(
    "",
    response_model=ProviderSpecialtyResponse,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_platform_admin)],
)
@transactional()
async def create_specialty(
    data: ProviderSpecialtyCreate,
    repo: ProviderSpecialtyRepository = Depends(get_provider_specialty_repository),
    db: AsyncSession = Depends(get_db),
):
    now = utc_now()
    specialty = ProviderSpecialtyEntity(
        id=ProviderSpecialtyId(generate_cuid()),
        code=data.code.strip().lower(),
        label=data.label.strip(),
        created_at=now,
        updated_at=now,
    )
    await repo.save_specialty(specialty)
    invalidate_reference_cache(_RESOURCE)
    return _response(specialty)


@router.post(
    "/{specialty_id}/retire",
    response_model=ProviderSpecialtyResponse,
    dependencies=[Depends(require_platform_admin)],
)
@transactional()
async def retire_specialty(
    specialty_id: str,
    request: Request,
    current_user: TokenData = Depends(require_platform_admin),
    repo: ProviderSpecialtyRepository = Depends(get_provider_specialty_repository),
    audit_handler=Depends(get_audit_event_handler),
    db: AsyncSession = Depends(get_db),
):
    """Stops new selection. Existing links stay readable on historical records."""
    specialty = await repo.get_specialty(ProviderSpecialtyId(specialty_id))
    if specialty is None:
        raise NotFoundError(
            "Specialty not found", resource_type="ProviderSpecialty", resource_id=specialty_id
        )
    specialty.retire(UserId(current_user.user_id), at=utc_now())
    await repo.save_specialty(specialty)
    await audit_change(specialty, audit_handler, current_user, request, tenant_id="platform")
    invalidate_reference_cache(_RESOURCE)
    return _response(specialty)


@router.get("/links", response_model=list[ProviderSpecialtyLinkResponse])
@readonly()
async def list_links(
    provider_id: str = Query(...),
    tenant_id: str = Query(...),
    current_user: TokenData = Depends(require_same_tenant),
    repo: ProviderSpecialtyRepository = Depends(get_provider_specialty_repository),
):
    """Includes links to retired specialties, flagged by specialty_is_active."""
    links = await repo.list_links_for_provider(TenantId(tenant_id), ProviderId(provider_id))
    catalogue = {s.id.value: s for s in await repo.list_specialties(include_inactive=True)}
    return [
        ProviderSpecialtyLinkResponse(
            id=link.id.value,
            tenant_id=link.tenant_id.value,
            provider_id=link.provider_id.value,
            specialty_id=link.specialty_id.value,
            specialty_code=catalogue[link.specialty_id.value].code,
            specialty_label=catalogue[link.specialty_id.value].label,
            specialty_is_active=catalogue[link.specialty_id.value].is_active,
        )
        for link in links
        if link.specialty_id.value in catalogue
    ]


@router.post(
    "/links",
    response_model=ProviderSpecialtyLinkResponse,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_not_viewer)],
)
@transactional()
async def add_link(
    data: ProviderSpecialtyLinkCreate,
    tenant_id: str = Query(...),
    current_user: TokenData = Depends(require_same_tenant),
    repo: ProviderSpecialtyRepository = Depends(get_provider_specialty_repository),
    db: AsyncSession = Depends(get_db),
):
    """A tenant selects an active catalogue entry for one of its practitioners."""
    specialty = await repo.get_specialty(ProviderSpecialtyId(data.specialty_id))
    if specialty is None:
        raise NotFoundError(
            "Specialty not found",
            resource_type="ProviderSpecialty",
            resource_id=data.specialty_id,
        )
    if not specialty.is_active:
        raise DomainError(
            f"Specialty {specialty.code!r} is retired and cannot be newly selected",
            http_status=422,
        )
    link = ProviderSpecialtyLinkEntity(
        id=ProviderSpecialtyLinkId(generate_cuid()),
        tenant_id=TenantId(tenant_id),
        provider_id=ProviderId(data.provider_id),
        specialty_id=specialty.id,
        created_at=utc_now(),
    )
    await repo.add_link(link)
    return ProviderSpecialtyLinkResponse(
        id=link.id.value,
        tenant_id=link.tenant_id.value,
        provider_id=link.provider_id.value,
        specialty_id=link.specialty_id.value,
        specialty_code=specialty.code,
        specialty_label=specialty.label,
        specialty_is_active=specialty.is_active,
    )


@router.delete(
    "/links/{link_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    dependencies=[Depends(require_not_viewer)],
)
@transactional()
async def remove_link(
    link_id: str,
    tenant_id: str = Query(...),
    current_user: TokenData = Depends(require_same_tenant),
    repo: ProviderSpecialtyRepository = Depends(get_provider_specialty_repository),
    db: AsyncSession = Depends(get_db),
):
    if not await repo.remove_link(TenantId(tenant_id), link_id):
        raise NotFoundError(
            "Specialty link not found",
            resource_type="ProviderSpecialtyLink",
            resource_id=link_id,
        )
