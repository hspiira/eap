"""Provider organisation API.

Deliberately not mounted under /providers: that prefix belongs to the
practitioner router, and straddling it would blur ownership and the generated
client's tags.
"""

from fastapi import APIRouter, Depends, Query, Request, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import get_audit_event_handler
from app.api.dependencies.pagination import PageParams, pagination
from app.api.dependencies.provider_network import get_provider_organisation_repository
from app.api.schemas.provider_network_schemas import (
    ProviderOrganisationCreate,
    ProviderOrganisationListResponse,
    ProviderOrganisationResponse,
    ProviderOrganisationUpdate,
    ReasonRequest,
)
from app.application.use_cases.provider_network_use_cases import (
    ChangeOrganisationApprovalUseCase,
    CreateOrganisationUseCase,
    OrganisationInput,
    SetOrganisationActiveUseCase,
)
from app.core.authorization import require_not_viewer, require_same_tenant, require_tenant_role
from app.core.database import get_db
from app.core.security import TokenData
from app.domain.entities.provider_organisation import ProviderOrganisationEntity
from app.domain.enums.provider_network import OrganisationApprovalStatus
from app.domain.enums.tenancy import TenantRole
from app.domain.exceptions import NotFoundError
from app.domain.repositories.provider_network_repository import (
    ProviderOrganisationRepository,
)
from app.domain.value_objects.core import TenantId, UserId
from app.domain.value_objects.provider_network import ProviderOrganisationId
from app.shared.decorators import readonly, transactional
from app.shared.utils.datetime import utc_now
from app.shared.utils.route_audit_helper import audit_change

router = APIRouter(prefix="/provider-organisations", tags=["provider-organisations"])

_APPROVAL_COMMANDS = {
    "approve": OrganisationApprovalStatus.APPROVED,
    "suspend": OrganisationApprovalStatus.SUSPENDED,
    "revoke": OrganisationApprovalStatus.REVOKED,
}


def _response(organisation: ProviderOrganisationEntity) -> ProviderOrganisationResponse:
    return ProviderOrganisationResponse(
        id=organisation.id.value,
        tenant_id=organisation.tenant_id.value,
        name=organisation.name,
        registration_number=organisation.registration_number,
        contact_email=organisation.contact_email,
        contact_phone=organisation.contact_phone,
        is_active=organisation.is_active,
        approval_status=organisation.approval_status,
        created_at=organisation.created_at,
        updated_at=organisation.updated_at,
    )


async def _require(
    repo: ProviderOrganisationRepository, tenant_id: str, organisation_id: str
) -> ProviderOrganisationEntity:
    organisation = await repo.get_organisation(
        TenantId(tenant_id), ProviderOrganisationId(organisation_id)
    )
    if organisation is None:
        raise NotFoundError(
            "Provider organisation not found",
            resource_type="ProviderOrganisation",
            resource_id=organisation_id,
        )
    return organisation


@router.get("", response_model=ProviderOrganisationListResponse)
@readonly()
async def list_organisations(
    tenant_id: str = Query(...),
    search: str | None = Query(None, description="Matches name or registration number"),
    is_active: bool | None = Query(None),
    approval_status: OrganisationApprovalStatus | None = Query(None),
    sort_by: str = Query("name", pattern="^(name|created_at|updated_at)$"),
    sort_desc: bool = Query(False),
    pg: PageParams = Depends(pagination()),
    current_user: TokenData = Depends(require_same_tenant),
    repo: ProviderOrganisationRepository = Depends(get_provider_organisation_repository),
):
    """Filtered and counted in SQL, so `total` covers the full matching set."""
    items, total = await repo.list_organisations(
        TenantId(tenant_id),
        search=search,
        is_active=is_active,
        approval_status=approval_status.value if approval_status else None,
        sort_by=sort_by,
        sort_desc=sort_desc,
        limit=pg.limit,
        offset=pg.offset,
    )
    return ProviderOrganisationListResponse(
        items=[_response(o) for o in items],
        total=total,
        page=pg.page,
        limit=pg.limit,
        has_more=(pg.offset + len(items)) < total,
    )


@router.get("/{organisation_id}", response_model=ProviderOrganisationResponse)
@readonly()
async def get_organisation(
    organisation_id: str,
    tenant_id: str = Query(...),
    current_user: TokenData = Depends(require_same_tenant),
    repo: ProviderOrganisationRepository = Depends(get_provider_organisation_repository),
):
    return _response(await _require(repo, tenant_id, organisation_id))


@router.post(
    "",
    response_model=ProviderOrganisationResponse,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_not_viewer)],
)
@transactional()
async def create_organisation(
    data: ProviderOrganisationCreate,
    request: Request,
    tenant_id: str = Query(...),
    current_user: TokenData = Depends(require_same_tenant),
    repo: ProviderOrganisationRepository = Depends(get_provider_organisation_repository),
    audit_handler=Depends(get_audit_event_handler),
    db: AsyncSession = Depends(get_db),
):
    organisation = await CreateOrganisationUseCase(repo).execute(
        TenantId(tenant_id),
        OrganisationInput(
            name=data.name,
            registration_number=data.registration_number,
            contact_email=data.contact_email,
            contact_phone=data.contact_phone,
        ),
        UserId(current_user.user_id),
    )
    await audit_change(organisation, audit_handler, current_user, request)
    return _response(organisation)


@router.patch(
    "/{organisation_id}",
    response_model=ProviderOrganisationResponse,
    dependencies=[Depends(require_not_viewer)],
)
@transactional()
async def update_organisation(
    organisation_id: str,
    data: ProviderOrganisationUpdate,
    request: Request,
    tenant_id: str = Query(...),
    current_user: TokenData = Depends(require_same_tenant),
    repo: ProviderOrganisationRepository = Depends(get_provider_organisation_repository),
    audit_handler=Depends(get_audit_event_handler),
    db: AsyncSession = Depends(get_db),
):
    """Partial update of descriptive fields only.

    `is_active` and `approval_status` are absent from the schema, so a general
    edit cannot move the supplier's approval or retire the record.
    """
    organisation = await _require(repo, tenant_id, organisation_id)
    fields = data.model_dump(exclude_unset=True)
    if "name" in fields and fields["name"] is not None:
        organisation.name = fields["name"].strip()
    for field in ("registration_number", "contact_email", "contact_phone"):
        if field in fields:
            setattr(organisation, field, fields[field])
    organisation.updated_at = utc_now()
    await repo.save_organisation(organisation)
    await audit_change(organisation, audit_handler, current_user, request)
    return _response(organisation)


@router.post(
    "/{organisation_id}/{command}",
    response_model=ProviderOrganisationResponse,
    dependencies=[Depends(require_tenant_role(TenantRole.ADMIN))],
)
@transactional()
async def run_approval_command(
    organisation_id: str,
    command: str,
    data: ReasonRequest,
    request: Request,
    tenant_id: str = Query(...),
    current_user: TokenData = Depends(require_same_tenant),
    repo: ProviderOrganisationRepository = Depends(get_provider_organisation_repository),
    audit_handler=Depends(get_audit_event_handler),
    db: AsyncSession = Depends(get_db),
):
    """Admin-only approval and activation commands, each requiring a reason."""
    actor = UserId(current_user.user_id)
    if command in _APPROVAL_COMMANDS:
        organisation = await ChangeOrganisationApprovalUseCase(repo).execute(
            TenantId(tenant_id),
            ProviderOrganisationId(organisation_id),
            _APPROVAL_COMMANDS[command],
            actor,
            data.reason,
        )
    elif command in {"deactivate", "reactivate"}:
        organisation = await SetOrganisationActiveUseCase(repo).execute(
            TenantId(tenant_id),
            ProviderOrganisationId(organisation_id),
            active=command == "reactivate",
            actor=actor,
            reason=data.reason,
        )
    else:
        raise NotFoundError("Unknown organisation command", resource_id=command)
    await audit_change(organisation, audit_handler, current_user, request)
    return _response(organisation)
