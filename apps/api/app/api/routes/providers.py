"""Practitioner API.

The general PATCH may change ordinary contact and profile fields only. Panel,
tier, accreditation and activation move through the lifecycle commands below,
each Admin-only and each requiring a reason, so there is one audited path per
lifecycle change rather than two.
"""

from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import (
    get_audit_event_handler,
    get_provider_engagement_document_repository,
    get_provider_repository,
    get_service_session_repository,
)
from app.api.schemas.provider_schemas import (
    AccountLinkCommand,
    AccountUnlinkCommand,
    AccreditationCommand,
    EngagementDocumentResponse,
    EngagementDocumentUpsert,
    PanelStatusCommand,
    ProviderCreate,
    ProviderDeliveryOrganisationStat,
    ProviderDeliveryStatsResponse,
    ProviderListResponse,
    ProviderResponse,
    ProviderUpdate,
    StatusCommand,
    TierCommand,
)
from app.core.authorization import require_not_viewer, require_same_tenant, require_tenant_role
from app.core.database import get_db
from app.core.security import TokenData, get_current_user
from app.domain.entities.provider import UNSET, ProviderEntity
from app.domain.entities.provider_engagement_document import ProviderEngagementDocument
from app.domain.enums import (
    AccreditationStatus,
    BaseStatus,
    EngagementDocumentKind,
    PanelStatus,
    ProviderTier,
    TenantRole,
    UgandaRegion,
)
from app.domain.exceptions import ConflictError
from app.domain.repositories.provider_engagement_document_repository import (
    ProviderEngagementDocumentRepository,
)
from app.domain.repositories.provider_repository import ProviderListQuery, ProviderRepository
from app.domain.repositories.service_session_repository import (
    ProviderDeliveryStats,
    ServiceSessionRepository,
)
from app.domain.value_objects.core import ProviderId, ProviderProfile, TenantId, UserId
from app.domain.value_objects.ids import ProviderEngagementDocumentId
from app.shared.decorators import readonly, transactional
from app.shared.utils.datetime import utc_now
from app.shared.utils.generators import generate_cuid
from app.shared.utils.route_audit_helper import audit_change

router = APIRouter(prefix="/providers", tags=["providers"])

require_admin = require_tenant_role(TenantRole.ADMIN)


def _response(provider: ProviderEntity) -> ProviderResponse:
    if provider.provider_profile is None:
        raise HTTPException(status_code=409, detail="Provider profile is incomplete")
    return ProviderResponse(
        id=provider.id.value,
        tenant_id=provider.tenant_id.value,
        display_name=provider.display_name,
        formal_name=provider.formal_name,
        email=provider.contact_email,
        phone=provider.contact_phone,
        user_id=provider.user_id.value if provider.user_id else None,
        identity_provenance=provider.identity_provenance,
        status=provider.status,
        license_info=provider.license_info,
        provider_profile=provider.provider_profile,
        created_at=provider.created_at,
        updated_at=provider.updated_at,
    )


async def _load(
    provider_id: str, current_user: TokenData, repo: ProviderRepository
) -> ProviderEntity:
    provider = await repo.get_by_id(ProviderId(provider_id))
    if provider is None or provider.tenant_id.value != current_user.tenant_id:
        raise HTTPException(status_code=404, detail="Provider not found")
    return provider


async def _save_if_changed(
    provider: ProviderEntity,
    repo: ProviderRepository,
    audit_handler,
    current_user: TokenData,
    request: Request,
) -> ProviderResponse:
    """Persist and audit only when the command emitted an event.

    A no-op command must write neither state nor audit; an unconditional save
    would still stamp updated_at through the model's onupdate.
    """
    if provider.events:
        await repo.save(provider)
        await audit_change(provider, audit_handler, current_user, request)
    return _response(provider)


@router.get("", response_model=ProviderListResponse, summary="Practitioner directory")
@readonly()
async def list_providers(
    tenant_id: str = Query(...),
    search: str | None = Query(None, description="Matches display name or contact email"),
    tier: list[ProviderTier] = Query(default=[]),
    region: list[UgandaRegion] = Query(default=[]),
    panel_status: list[PanelStatus] = Query(default=[]),
    accreditation_status: list[AccreditationStatus] = Query(default=[]),
    provider_status: list[BaseStatus] = Query(default=[], alias="status"),
    has_account: bool | None = Query(None),
    page: int = Query(1, ge=1),
    limit: int = Query(50, ge=1, le=200),
    sort_by: str = Query("display_name", pattern="^(display_name|created_at|updated_at)$"),
    sort_desc: bool = Query(False),
    current_user: TokenData = Depends(require_same_tenant),
    repo: ProviderRepository = Depends(get_provider_repository),
    db: AsyncSession = Depends(get_db),
):
    """Filter, search, sort and paginate over the whole tenant dataset."""
    scope = TenantId(tenant_id)
    query = ProviderListQuery(
        search=search,
        tiers=tuple(tier),
        regions=tuple(region),
        panel_statuses=tuple(panel_status),
        accreditation_statuses=tuple(accreditation_status),
        statuses=tuple(provider_status),
        has_account=has_account,
        sort_by=sort_by,
        sort_desc=sort_desc,
        page=page,
        limit=limit,
    )
    providers = await repo.search(scope, query)
    total = await repo.count_matching(scope, query)
    return ProviderListResponse(
        items=[_response(provider) for provider in providers],
        total=total,
        page=page,
        limit=limit,
        has_more=query.offset + len(providers) < total,
    )


@router.get("/{provider_id}", response_model=ProviderResponse)
@readonly()
async def get_provider(
    provider_id: str,
    current_user: TokenData = Depends(get_current_user),
    repo: ProviderRepository = Depends(get_provider_repository),
    db: AsyncSession = Depends(get_db),
):
    return _response(await _load(provider_id, current_user, repo))


@router.post(
    "",
    response_model=ProviderResponse,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_not_viewer)],
    summary="Create a practitioner, with no account and no lifecycle standing",
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
    now = utc_now()
    provider = ProviderEntity(
        id=ProviderId(generate_cuid()),
        tenant_id=TenantId(tenant_id),
        user_id=None,
        display_name=data.display_name.strip(),
        contact_email=str(data.email) if data.email else None,
        contact_phone=data.phone,
        status=BaseStatus.PENDING,
        provider_profile=ProviderProfile(
            tier=data.tier,
            region=data.region,
            accreditation_status=AccreditationStatus.PENDING,
            panel_status=PanelStatus.PENDING,
            bio=data.bio,
            gender=data.gender,
            title=data.title,
        ),
        license_info=data.license_info,
        created_at=now,
        updated_at=now,
    )
    provider.record_created(UserId(current_user.user_id))
    return await _save_if_changed(provider, repo, audit_handler, current_user, request)


@router.patch(
    "/{provider_id}",
    response_model=ProviderResponse,
    dependencies=[Depends(require_not_viewer)],
    summary="Partial update of ordinary contact and profile fields",
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
    provider = await _load(provider_id, current_user, repo)
    provided = data.model_fields_set
    provider.apply_profile_changes(
        UserId(current_user.user_id),
        display_name=data.display_name if "display_name" in provided else UNSET,
        contact_email=(str(data.email) if data.email else None) if "email" in provided else UNSET,
        contact_phone=data.phone if "phone" in provided else UNSET,
        title=data.title if "title" in provided else UNSET,
        license_info=data.license_info if "license_info" in provided else UNSET,
        region=data.region if "region" in provided else UNSET,
        bio=data.bio if "bio" in provided else UNSET,
        gender=data.gender if "gender" in provided else UNSET,
    )
    return await _save_if_changed(provider, repo, audit_handler, current_user, request)


@router.patch(
    "/{provider_id}/tier",
    response_model=ProviderResponse,
    dependencies=[Depends(require_admin)],
    summary="Audited tier change",
)
@transactional()
async def change_tier(
    provider_id: str,
    data: TierCommand,
    request: Request,
    current_user: TokenData = Depends(get_current_user),
    repo: ProviderRepository = Depends(get_provider_repository),
    audit_handler=Depends(get_audit_event_handler),
    db: AsyncSession = Depends(get_db),
):
    provider = await _load(provider_id, current_user, repo)
    provider.change_tier(data.tier, UserId(current_user.user_id), data.reason)
    return await _save_if_changed(provider, repo, audit_handler, current_user, request)


@router.patch(
    "/{provider_id}/panel-status",
    response_model=ProviderResponse,
    dependencies=[Depends(require_admin)],
    summary="Audited panel-status change",
)
@transactional()
async def change_panel_status(
    provider_id: str,
    data: PanelStatusCommand,
    request: Request,
    current_user: TokenData = Depends(get_current_user),
    repo: ProviderRepository = Depends(get_provider_repository),
    audit_handler=Depends(get_audit_event_handler),
    db: AsyncSession = Depends(get_db),
):
    provider = await _load(provider_id, current_user, repo)
    provider.change_panel_status(data.panel_status, UserId(current_user.user_id), data.reason)
    return await _save_if_changed(provider, repo, audit_handler, current_user, request)


@router.patch(
    "/{provider_id}/accreditation",
    response_model=ProviderResponse,
    dependencies=[Depends(require_admin)],
    summary="Audited accreditation change",
)
@transactional()
async def change_accreditation(
    provider_id: str,
    data: AccreditationCommand,
    request: Request,
    current_user: TokenData = Depends(get_current_user),
    repo: ProviderRepository = Depends(get_provider_repository),
    audit_handler=Depends(get_audit_event_handler),
    db: AsyncSession = Depends(get_db),
):
    provider = await _load(provider_id, current_user, repo)
    provided = data.model_fields_set
    provider.change_accreditation(
        UserId(current_user.user_id),
        data.reason,
        accreditation_status=data.accreditation_status,
        accreditation_authority=(
            data.accreditation_authority if "accreditation_authority" in provided else UNSET
        ),
        accreditation_expiry=(
            data.accreditation_expiry if "accreditation_expiry" in provided else UNSET
        ),
    )
    return await _save_if_changed(provider, repo, audit_handler, current_user, request)


@router.patch(
    "/{provider_id}/status",
    response_model=ProviderResponse,
    dependencies=[Depends(require_admin)],
    summary="Audited activation or deactivation",
)
@transactional()
async def change_status(
    provider_id: str,
    data: StatusCommand,
    request: Request,
    current_user: TokenData = Depends(get_current_user),
    repo: ProviderRepository = Depends(get_provider_repository),
    audit_handler=Depends(get_audit_event_handler),
    db: AsyncSession = Depends(get_db),
):
    provider = await _load(provider_id, current_user, repo)
    provider.change_status(data.status, UserId(current_user.user_id), data.reason)
    return await _save_if_changed(provider, repo, audit_handler, current_user, request)


@router.post(
    "/{provider_id}/account-link",
    response_model=ProviderResponse,
    dependencies=[Depends(require_admin)],
    summary="Link a same-tenant user account. Grants no role and copies no contact data",
)
@transactional()
async def link_account(
    provider_id: str,
    data: AccountLinkCommand,
    request: Request,
    current_user: TokenData = Depends(get_current_user),
    repo: ProviderRepository = Depends(get_provider_repository),
    audit_handler=Depends(get_audit_event_handler),
    db: AsyncSession = Depends(get_db),
):
    provider = await _load(provider_id, current_user, repo)
    target = UserId(data.user_id)
    if await repo.get_user_in_tenant(target, provider.tenant_id) is None:
        raise HTTPException(status_code=404, detail="User not found in tenant")
    existing = await repo.get_by_user_id(provider.tenant_id, target)
    if existing is not None and existing.id != provider.id:
        raise ConflictError(
            "That account is already linked to another practitioner",
            details={"user_id": data.user_id, "provider_id": existing.id.value},
        )
    provider.link_account(target, UserId(current_user.user_id), data.reason)
    return await _save_if_changed(provider, repo, audit_handler, current_user, request)


@router.delete(
    "/{provider_id}/account-link",
    response_model=ProviderResponse,
    dependencies=[Depends(require_admin)],
    summary="Unlink the account. The practitioner and their sessions remain visible",
)
@transactional()
async def unlink_account(
    provider_id: str,
    data: AccountUnlinkCommand,
    request: Request,
    current_user: TokenData = Depends(get_current_user),
    repo: ProviderRepository = Depends(get_provider_repository),
    audit_handler=Depends(get_audit_event_handler),
    db: AsyncSession = Depends(get_db),
):
    provider = await _load(provider_id, current_user, repo)
    provider.unlink_account(UserId(current_user.user_id), data.reason)
    return await _save_if_changed(provider, repo, audit_handler, current_user, request)


def _document_response(document: ProviderEngagementDocument) -> EngagementDocumentResponse:
    return EngagementDocumentResponse(
        id=document.id.value,
        tenant_id=document.tenant_id.value,
        provider_id=document.provider_id.value,
        document_kind=document.document_kind,
        state=document.state,
        note=document.note,
        created_at=document.created_at,
        updated_at=document.updated_at,
    )


@router.get(
    "/{provider_id}/engagement-documents",
    response_model=list[EngagementDocumentResponse],
    summary="The engagement-document checklist for one practitioner",
)
@readonly()
async def list_engagement_documents(
    provider_id: str,
    current_user: TokenData = Depends(get_current_user),
    repo: ProviderRepository = Depends(get_provider_repository),
    documents: ProviderEngagementDocumentRepository = Depends(
        get_provider_engagement_document_repository
    ),
    db: AsyncSession = Depends(get_db),
):
    provider = await _load(provider_id, current_user, repo)
    entries = await documents.list_for_provider(provider.tenant_id, provider.id)
    return [_document_response(entry) for entry in entries]


@router.put(
    "/{provider_id}/engagement-documents/{document_kind}",
    response_model=EngagementDocumentResponse,
    dependencies=[Depends(require_admin)],
    summary="Audited upsert of one checklist entry",
)
@transactional()
async def upsert_engagement_document(
    provider_id: str,
    document_kind: EngagementDocumentKind,
    data: EngagementDocumentUpsert,
    request: Request,
    current_user: TokenData = Depends(get_current_user),
    repo: ProviderRepository = Depends(get_provider_repository),
    documents: ProviderEngagementDocumentRepository = Depends(
        get_provider_engagement_document_repository
    ),
    audit_handler=Depends(get_audit_event_handler),
    db: AsyncSession = Depends(get_db),
):
    provider = await _load(provider_id, current_user, repo)
    note = data.note.strip() if data.note and data.note.strip() else None
    actor = UserId(current_user.user_id)
    document = await documents.get_for_kind(provider.tenant_id, provider.id, document_kind)
    if document is None:
        now = utc_now()
        document = ProviderEngagementDocument(
            id=ProviderEngagementDocumentId(generate_cuid()),
            tenant_id=provider.tenant_id,
            provider_id=provider.id,
            document_kind=document_kind,
            state=data.state,
            note=note,
            created_at=now,
            updated_at=now,
        )
        document.record_created(actor)
    else:
        document.update_record(data.state, note, actor)
    if document.events:
        await documents.save(document)
        await audit_change(document, audit_handler, current_user, request)
    return _document_response(document)


def _delivery_stats_response(stats: ProviderDeliveryStats) -> ProviderDeliveryStatsResponse:
    return ProviderDeliveryStatsResponse(
        total_sessions=stats.total_sessions,
        first_session_at=stats.first_session_at,
        last_session_at=stats.last_session_at,
        by_delivery_context={
            context.value: count for context, count in stats.by_delivery_context.items()
        },
        by_organisation=[
            ProviderDeliveryOrganisationStat(
                organisation_id=row.organisation_id,
                organisation_name=row.organisation_name,
                session_count=row.session_count,
            )
            for row in stats.by_organisation
        ],
    )


@router.get(
    "/{provider_id}/delivery-stats",
    response_model=ProviderDeliveryStatsResponse,
    summary="Counts over one practitioner's whole delivery record",
)
@readonly()
async def get_delivery_stats(
    provider_id: str,
    current_user: TokenData = Depends(get_current_user),
    repo: ProviderRepository = Depends(get_provider_repository),
    sessions: ServiceSessionRepository = Depends(get_service_session_repository),
    db: AsyncSession = Depends(get_db),
):
    """The organisation breakdown follows each session's stored affiliation.

    A practitioner who moves between organisations keeps the attribution their
    past sessions were delivered under (decision 2).
    """
    provider = await _load(provider_id, current_user, repo)
    return _delivery_stats_response(
        await sessions.provider_delivery_stats(provider.tenant_id, provider.id)
    )
