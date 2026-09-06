"""Dated affiliation API.

Validity is start-inclusive and end-exclusive: an affiliation with
`valid_until` 2026-07-01 does not cover 2026-07-01.
"""

from datetime import date

from fastapi import APIRouter, Depends, Query, Request, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import get_audit_event_handler
from app.api.dependencies.pagination import PageParams, pagination
from app.api.dependencies.provider_network import (
    get_provider_affiliation_repository,
    get_provider_organisation_repository,
)
from app.api.schemas.provider_network_schemas import (
    ProviderAffiliationCreate,
    ProviderAffiliationEndUpdate,
    ProviderAffiliationListResponse,
    ProviderAffiliationResponse,
)
from app.application.use_cases.provider_network_use_cases import (
    ChangeAffiliationEndUseCase,
    CreateAffiliationUseCase,
)
from app.core.authorization import require_not_viewer, require_same_tenant
from app.core.database import get_db
from app.core.security import TokenData
from app.domain.entities.provider_affiliation import ProviderAffiliationEntity
from app.domain.entities.provider_organisation import ProviderOrganisationEntity
from app.domain.exceptions import NotFoundError
from app.domain.repositories.provider_network_repository import (
    ProviderAffiliationRepository,
    ProviderOrganisationRepository,
)
from app.domain.value_objects.core import ProviderId, TenantId, UserId
from app.domain.value_objects.provider_network import (
    ProviderAffiliationId,
    ProviderOrganisationId,
)
from app.shared.decorators import readonly, transactional
from app.shared.utils.route_audit_helper import audit_change

router = APIRouter(prefix="/provider-affiliations", tags=["provider-affiliations"])


def _response(
    affiliation: ProviderAffiliationEntity, organisation: ProviderOrganisationEntity
) -> ProviderAffiliationResponse:
    """The organisation fields are its current state, not a historical snapshot.

    Which organisation delivered still comes from the stored affiliation, so a
    firm changing its name does not reattribute past work.
    """
    return ProviderAffiliationResponse(
        id=affiliation.id.value,
        tenant_id=affiliation.tenant_id.value,
        provider_id=affiliation.provider_id.value,
        organisation_id=affiliation.organisation_id.value,
        valid_from=affiliation.valid_from,
        valid_until=affiliation.valid_until,
        organisation_name=organisation.name,
        organisation_is_active=organisation.is_active,
        organisation_approval_status=organisation.approval_status,
        created_at=affiliation.created_at,
        updated_at=affiliation.updated_at,
    )


async def _with_organisations(
    organisations: ProviderOrganisationRepository,
    tenant_id: str,
    affiliations: list[ProviderAffiliationEntity],
) -> list[ProviderAffiliationResponse]:
    by_id = await organisations.get_organisations_by_ids(
        TenantId(tenant_id), [a.organisation_id for a in affiliations]
    )
    return [
        _response(a, by_id[a.organisation_id.value])
        for a in affiliations
        if a.organisation_id.value in by_id
    ]


@router.get("", response_model=ProviderAffiliationListResponse)
@readonly()
async def list_affiliations(
    tenant_id: str = Query(...),
    provider_id: str | None = Query(None),
    organisation_id: str | None = Query(None),
    valid_at: date | None = Query(
        None, description="Affiliations covering this day, end-exclusive"
    ),
    include_ended: bool = Query(False),
    pg: PageParams = Depends(pagination()),
    current_user: TokenData = Depends(require_same_tenant),
    repo: ProviderAffiliationRepository = Depends(get_provider_affiliation_repository),
    organisations: ProviderOrganisationRepository = Depends(get_provider_organisation_repository),
):
    items, total = await repo.list_affiliations(
        TenantId(tenant_id),
        provider_id=ProviderId(provider_id) if provider_id else None,
        organisation_id=ProviderOrganisationId(organisation_id) if organisation_id else None,
        valid_at=valid_at,
        include_ended=include_ended,
        limit=pg.limit,
        offset=pg.offset,
    )
    return ProviderAffiliationListResponse(
        items=await _with_organisations(organisations, tenant_id, list(items)),
        total=total,
        page=pg.page,
        limit=pg.limit,
        has_more=(pg.offset + len(items)) < total,
    )


@router.post(
    "",
    response_model=ProviderAffiliationResponse,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_not_viewer)],
)
@transactional()
async def create_affiliation(
    data: ProviderAffiliationCreate,
    request: Request,
    organisation_id: str = Query(..., description="Organisation the practitioner joins"),
    tenant_id: str = Query(...),
    current_user: TokenData = Depends(require_same_tenant),
    repo: ProviderAffiliationRepository = Depends(get_provider_affiliation_repository),
    organisations: ProviderOrganisationRepository = Depends(get_provider_organisation_repository),
    audit_handler=Depends(get_audit_event_handler),
    db: AsyncSession = Depends(get_db),
):
    """Rejects an interval overlapping another affiliation for the same pair.

    Concurrent affiliations with different organisations are allowed.
    """
    affiliation = await CreateAffiliationUseCase(repo, organisations).execute(
        TenantId(tenant_id),
        provider_id=ProviderId(data.provider_id),
        organisation_id=ProviderOrganisationId(organisation_id),
        valid_from=data.valid_from,
        valid_until=data.valid_until,
        actor=UserId(current_user.user_id),
    )
    await audit_change(affiliation, audit_handler, current_user, request)
    responses = await _with_organisations(organisations, tenant_id, [affiliation])
    return responses[0]


@router.patch(
    "/{affiliation_id}",
    response_model=ProviderAffiliationResponse,
    dependencies=[Depends(require_not_viewer)],
)
@transactional()
async def change_affiliation_end(
    affiliation_id: str,
    data: ProviderAffiliationEndUpdate,
    request: Request,
    tenant_id: str = Query(...),
    current_user: TokenData = Depends(require_same_tenant),
    repo: ProviderAffiliationRepository = Depends(get_provider_affiliation_repository),
    organisations: ProviderOrganisationRepository = Depends(get_provider_organisation_repository),
    audit_handler=Depends(get_audit_event_handler),
    db: AsyncSession = Depends(get_db),
):
    """Moves the end date only. The practitioner and organisation are immutable."""
    affiliation = await ChangeAffiliationEndUseCase(repo).execute(
        TenantId(tenant_id),
        ProviderAffiliationId(affiliation_id),
        valid_until=data.valid_until,
        actor=UserId(current_user.user_id),
        reason=data.reason,
    )
    await audit_change(affiliation, audit_handler, current_user, request)
    responses = await _with_organisations(organisations, tenant_id, [affiliation])
    if not responses:
        raise NotFoundError(
            "Provider organisation not found",
            resource_type="ProviderOrganisation",
            resource_id=affiliation.organisation_id.value,
        )
    return responses[0]
