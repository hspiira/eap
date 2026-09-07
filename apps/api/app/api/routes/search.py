"""Global search API.

One authenticated, tenant-scoped read over the record categories the header
dialog offers: clients, practitioners and provider organisations. It reuses
each module's existing repository query, so search cannot see further than
the module it searches, and detail routes still authorise their own reads.

Every category is bounded and its results are projected, not returned whole.
A category that fails is reported as failed rather than as empty.

The query travels in a request body rather than a query string. It is
user-entered text that routinely names a person, and a URL parameter is
recorded by the server access log and by every proxy in front of it whatever
the handler itself does. This module logs neither the query nor any exception
string that would carry it.
"""

import logging

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import get_client_repository, get_provider_repository
from app.api.dependencies.provider_network import get_provider_organisation_repository
from app.api.schemas.search_schemas import (
    MIN_QUERY_LENGTH,
    GlobalSearchRequest,
    GlobalSearchResponse,
    SearchCategoryResult,
    SearchResultItem,
)
from app.core.authorization import require_same_tenant
from app.core.database import get_db
from app.core.security import TokenData
from app.domain.entities.client import ClientEntity
from app.domain.entities.provider import ProviderEntity
from app.domain.entities.provider_organisation import ProviderOrganisationEntity
from app.domain.repositories.client_repository import ClientRepository
from app.domain.repositories.provider_network_repository import ProviderOrganisationRepository
from app.domain.repositories.provider_repository import ProviderListQuery, ProviderRepository
from app.domain.value_objects.core import TenantId
from app.shared.decorators import readonly

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/search", tags=["search"])

_EMPTY = SearchCategoryResult(items=[], has_more=False, failed=False)
_FAILED = SearchCategoryResult(items=[], has_more=False, failed=True)


def _client_item(client: ClientEntity) -> SearchResultItem:
    return SearchResultItem(
        id=client.id.value,
        label=client.name,
        secondary=client.code,
        type="client",
    )


def _practitioner_item(provider: ProviderEntity) -> SearchResultItem:
    profile = provider.provider_profile
    parts = [v.value for v in ((profile.tier, profile.region) if profile else ()) if v]
    secondary = " · ".join(parts) if parts else None
    return SearchResultItem(
        id=provider.id.value,
        label=provider.display_name,
        secondary=secondary,
        type="practitioner",
    )


def _organisation_item(
    organisation: ProviderOrganisationEntity,
) -> SearchResultItem:
    return SearchResultItem(
        id=organisation.id.value,
        label=organisation.name,
        secondary=organisation.registration_number,
        type="provider_organisation",
    )


def _bounded(items: list[SearchResultItem], limit: int) -> SearchCategoryResult:
    """Truncate to the limit and report that more exist, without a count.

    Callers over-fetch by one row. That is what establishes has_more, so no
    query counts records the caller may not read.
    """
    return SearchCategoryResult(
        items=items[:limit],
        has_more=len(items) > limit,
        failed=False,
    )


async def _search_clients(
    repo: ClientRepository, tenant: TenantId, query: str, limit: int
) -> SearchCategoryResult:
    """Client names and tenant-scoped aliases. Archived clients stay out."""
    clients = await repo.list_all(
        tenant_id=tenant,
        search=query,
        limit=limit + 1,
        offset=0,
        sort_by="name",
        sort_desc=False,
    )
    return _bounded([_client_item(client) for client in clients], limit)


async def _search_practitioners(
    repo: ProviderRepository, tenant: TenantId, query: str, limit: int
) -> SearchCategoryResult:
    """Practitioner display name and contact email, via the directory query."""
    providers = await repo.search(
        tenant,
        ProviderListQuery(search=query, sort_by="display_name", page=1, limit=limit + 1),
    )
    return _bounded([_practitioner_item(provider) for provider in providers], limit)


async def _search_organisations(
    repo: ProviderOrganisationRepository, tenant: TenantId, query: str, limit: int
) -> SearchCategoryResult:
    """Organisation name and registration number."""
    organisations, _ = await repo.list_organisations(
        tenant,
        search=query,
        sort_by="name",
        sort_desc=False,
        limit=limit + 1,
        offset=0,
    )
    return _bounded([_organisation_item(o) for o in organisations], limit)


async def _run_category(name: str, coro, db: AsyncSession) -> SearchCategoryResult:
    """Isolate one category's failure from the rest of the response.

    Rolls back so a failed statement does not poison the categories that
    follow. Logs the category and the exception class only: an exception
    string from SQLAlchemy carries the statement and its parameters, and the
    parameter here is the caller's raw search text.
    """
    try:
        return await coro
    except Exception as exc:  # noqa: BLE001 - a category failure must not fail the response
        logger.error("global search category %s failed: %s", name, type(exc).__name__)
        await db.rollback()
        return _FAILED


@router.post(
    "",
    response_model=GlobalSearchResponse,
    summary="Search records the caller may already read",
)
@readonly()
async def global_search(
    body: GlobalSearchRequest,
    tenant_id: str = Query(..., description="Tenant identifier"),
    _current_user: TokenData = Depends(require_same_tenant),
    client_repo: ClientRepository = Depends(get_client_repository),
    provider_repo: ProviderRepository = Depends(get_provider_repository),
    organisation_repo: ProviderOrganisationRepository = Depends(
        get_provider_organisation_repository
    ),
    db: AsyncSession = Depends(get_db),
) -> GlobalSearchResponse:
    """Bounded, projected matches per category, scoped to the caller's tenant.

    A POST that reads: the verb is what keeps the search term out of the URL.
    Nothing here writes, and the route is wrapped read-only so nothing commits.

    Tenant comes from the authenticated context, which `require_same_tenant`
    compares against the requested tenant before any query runs.
    """
    query = body.q.strip()
    limit = body.limit
    if len(query) < MIN_QUERY_LENGTH:
        return GlobalSearchResponse(
            clients=_EMPTY, practitioners=_EMPTY, provider_organisations=_EMPTY
        )

    tenant = TenantId(tenant_id)
    return GlobalSearchResponse(
        clients=await _run_category(
            "clients", _search_clients(client_repo, tenant, query, limit), db
        ),
        practitioners=await _run_category(
            "practitioners", _search_practitioners(provider_repo, tenant, query, limit), db
        ),
        provider_organisations=await _run_category(
            "provider_organisations",
            _search_organisations(organisation_repo, tenant, query, limit),
            db,
        ),
    )
