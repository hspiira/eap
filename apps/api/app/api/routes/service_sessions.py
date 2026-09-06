"""
Service Session API Routes

FastAPI routes for Service Session operations.
Refactored to use @transactional decorator to eliminate try/except boilerplate.
"""

from collections.abc import Sequence
from datetime import datetime

from fastapi import APIRouter, Depends, Query, Request, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import (
    PageParams,
    get_audit_event_handler,
    get_authorization_repository,
    get_case_repository,
    get_eligible_member_repository,
    get_provider_repository,
    get_service_repository,
    get_service_session_repository,
    get_session_attribution_reader,
    pagination,
)
from app.api.dependencies.provider_network import (
    get_provider_affiliation_repository,
    get_provider_organisation_repository,
)
from app.api.schemas.service_session_schemas import (
    ServiceSessionCancelRequest,
    ServiceSessionCompleteRequest,
    ServiceSessionCompleteResponse,
    ServiceSessionCreate,
    ServiceSessionListResponse,
    ServiceSessionRescheduleRequest,
    ServiceSessionResponse,
    ServiceSessionUpdate,
    ServiceSessionUpdateFeedback,
    SessionDrawdownResponse,
)
from app.application.use_cases.authorization_drawdown import (
    ConsumeAuthorizationForSessionUseCase,
)
from app.application.use_cases.service_session_use_cases import (
    CreateServiceSessionUseCase,
    GetServiceSessionUseCase,
    UpdateServiceSessionUseCase,
)
from app.application.use_cases.transitions import (
    ServiceSessionTransition,
    TransitionUseCase,
)
from app.core.authorization import (
    get_service_session_for_current_tenant,
    require_not_viewer,
    require_same_tenant,
)
from app.core.database import get_db
from app.core.security import TokenData, get_current_user
from app.domain.entities.service_session import ServiceSessionEntity
from app.domain.enums import SessionDeliveryContext, SessionStatus
from app.domain.enums.provider_network import OrganisationApprovalStatus
from app.domain.exceptions import NotFoundError, ValidationException
from app.domain.repositories.case_repository import CaseRepository
from app.domain.repositories.eap_programme_repository import AuthorizationRepository
from app.domain.repositories.eligible_member_repository import EligibleMemberRepository
from app.domain.repositories.provider_network_repository import (
    ProviderAffiliationRepository,
    ProviderOrganisationRepository,
)
from app.domain.repositories.provider_repository import ProviderRepository
from app.domain.repositories.service_repository import ServiceRepository
from app.domain.repositories.service_session_repository import (
    ServiceSessionRepository,
)
from app.domain.repositories.session_attribution_reader import SessionAttributionReader
from app.domain.services.provider_eligibility import (
    AFFILIATION_NOT_FOUND,
    UNRESOLVED_AFFILIATION,
    EligibilityReason,
    direct_delivery_reasons,
    evaluate_organisation_delivery,
    evaluate_practitioner,
    missing_affiliation_reasons,
    require_eligible,
)
from app.domain.value_objects.core import (
    CaseId,
    EligibleMemberId,
    ProviderId,
    ServiceId,
    SessionId,
    TenantId,
)
from app.domain.value_objects.provider_network import ProviderAffiliationId
from app.shared.decorators import readonly, transactional
from app.shared.utils.datetime import ensure_utc, utc_now
from app.shared.utils.generators import generate_cuid
from app.shared.utils.route_audit_helper import audit_change

router = APIRouter(prefix="/service-sessions", tags=["service-sessions"])


def to_service_session_response(
    session: ServiceSessionEntity,
    provider_organisation_id: str | None = None,
) -> ServiceSessionResponse:
    """Map ServiceSessionEntity to API response using public properties."""
    return ServiceSessionResponse(
        id=session.id.value,
        tenant_id=session.tenant_id.value,
        service_id=session.service_id.value,
        provider_id=session.provider_id.value,
        member_id=session.member_id.value,
        scheduled_at=session.scheduled_at,
        delivery_context=session.delivery_context,
        provider_affiliation_id=session.provider_affiliation_id,
        provider_organisation_id=provider_organisation_id,
        status=session.status,
        reschedule_count=session.reschedule_count,
        completed_at=session.completed_at,
        duration=session.duration,
        location=session.location,
        notes=session.notes,
        feedback=session.feedback,
        cancellation_reason=session.cancellation_reason,
        is_active=session.is_active(),
        session_type=session.session_type,
        category=session.category,
        rate_ugx=session.rate_ugx,
        issue_topic=session.issue_topic,
        diagnosis_type_id=session.diagnosis_type_id,
        diagnosis_id=session.diagnosis_id,
        approved_by=session.approved_by,
        session_number=session.session_number,
        partner_name=session.partner_name,
        partner_relationship=session.partner_relationship,
        headcount=session.headcount,
        client_type=session.client_type,
        clinical_outcome=session.clinical_outcome,
    )


def _reject_unknown_context(context: SessionDeliveryContext) -> None:
    """Unknown delivery is historical evidence, never a live booking."""
    if context is SessionDeliveryContext.UNKNOWN:
        raise ValidationException(
            "A booking must state Direct or Organisation delivery. Unknown records a "
            "historical session whose source carries no evidence of the arrangement.",
            field="delivery_context",
        )


async def _require_bookable(
    provider_repo: ProviderRepository,
    tenant_id: TenantId,
    provider_id: ProviderId,
    scheduled_at: datetime,
    *,
    delivery_context: SessionDeliveryContext,
    affiliation_id: str | None,
    affiliation_repo: ProviderAffiliationRepository,
    organisation_repo: ProviderOrganisationRepository,
) -> None:
    """Apply the whole booking gate inside the caller's transaction.

    The practitioner is read under a row lock, so a preview cannot authorise a
    booking that a concurrent suspension has already invalidated. Organisation
    delivery adds supplier approval and affiliation validity to the same
    decision, and every failing reason is reported rather than the first.
    """
    provider = await provider_repo.get_for_booking(tenant_id, provider_id)
    if provider is None:
        raise NotFoundError(
            "Provider not found", resource_type="Provider", resource_id=provider_id.value
        )
    decision = evaluate_practitioner(provider, scheduled_at=scheduled_at, now=utc_now())
    decision = decision.extend(
        await _delivery_reasons(
            tenant_id,
            provider_id,
            scheduled_at,
            delivery_context=delivery_context,
            affiliation_id=affiliation_id,
            affiliation_repo=affiliation_repo,
            organisation_repo=organisation_repo,
        )
    )
    require_eligible(decision, provider_id.value)


async def _delivery_reasons(
    tenant_id: TenantId,
    provider_id: ProviderId,
    scheduled_at: datetime,
    *,
    delivery_context: SessionDeliveryContext,
    affiliation_id: str | None,
    affiliation_repo: ProviderAffiliationRepository,
    organisation_repo: ProviderOrganisationRepository,
) -> tuple[EligibilityReason, ...]:
    """What the chosen delivery arrangement adds to the practitioner's own gate."""
    if delivery_context is not SessionDeliveryContext.ORGANISATION:
        return direct_delivery_reasons(affiliation_id)
    missing = missing_affiliation_reasons(affiliation_id)
    if missing:
        return missing
    affiliation = await affiliation_repo.get_valid_affiliation(
        tenant_id,
        ProviderAffiliationId(affiliation_id),
        provider_id=provider_id,
        at=scheduled_at,
    )
    if affiliation is None:
        return (UNRESOLVED_AFFILIATION,)
    organisation = await organisation_repo.get_organisation(tenant_id, affiliation.organisation_id)
    if organisation is None:
        return (AFFILIATION_NOT_FOUND,)
    return evaluate_organisation_delivery(
        organisation.is_active,
        organisation.approval_status is OrganisationApprovalStatus.APPROVED,
    )


async def _one(
    session: ServiceSessionEntity, reader: SessionAttributionReader
) -> ServiceSessionResponse:
    """One session, with the organisation resolved from its own affiliation."""
    return (await _many([session], reader))[0]


async def _many(
    sessions: Sequence[ServiceSessionEntity], reader: SessionAttributionReader
) -> list[ServiceSessionResponse]:
    """Sessions with attribution resolved in one query rather than one per row.

    The organisation comes from the affiliation stored on each session, never
    from the practitioner's current affiliations, so moving firms does not
    reattribute delivery that already happened.
    """
    if not sessions:
        return []
    affiliation_ids = [s.provider_affiliation_id for s in sessions if s.provider_affiliation_id]
    organisations = await reader.organisation_ids_by_affiliation(
        sessions[0].tenant_id, affiliation_ids
    )
    return [
        to_service_session_response(
            session, organisations.get(session.provider_affiliation_id or "")
        )
        for session in sessions
    ]


# ==================== COMMANDS (Use Cases) ====================


@router.post(
    "/",
    response_model=ServiceSessionResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new service session",
    dependencies=[Depends(require_not_viewer)],
)
@transactional()
async def create_service_session(
    data: ServiceSessionCreate,
    request: Request,
    tenant_id: str = Query(..., description="Tenant identifier"),
    current_user: TokenData = Depends(require_same_tenant),
    session_repo: ServiceSessionRepository = Depends(get_service_session_repository),
    member_repo: EligibleMemberRepository = Depends(get_eligible_member_repository),
    provider_repo: ProviderRepository = Depends(get_provider_repository),
    service_repo: ServiceRepository = Depends(get_service_repository),
    affiliation_repo: ProviderAffiliationRepository = Depends(get_provider_affiliation_repository),
    organisation_repo: ProviderOrganisationRepository = Depends(
        get_provider_organisation_repository
    ),
    attribution_reader: SessionAttributionReader = Depends(get_session_attribution_reader),
    audit_handler=Depends(get_audit_event_handler),
    db: AsyncSession = Depends(get_db),
):
    """Create a new service session."""
    member = await member_repo.get_by_id(EligibleMemberId(data.member_id))
    if member is None or member.tenant_id.value != tenant_id:
        raise NotFoundError("Member not found", resource_type="Member", resource_id=data.member_id)
    scheduled_at = ensure_utc(data.scheduled_at)
    _reject_unknown_context(data.delivery_context)
    await _require_bookable(
        provider_repo,
        TenantId(tenant_id),
        ProviderId(data.provider_id),
        scheduled_at,
        delivery_context=data.delivery_context,
        affiliation_id=data.provider_affiliation_id,
        affiliation_repo=affiliation_repo,
        organisation_repo=organisation_repo,
    )
    service = await service_repo.get_by_id(ServiceId(data.service_id))
    if service is None or service.tenant_id.value != tenant_id:
        raise NotFoundError(
            "Service not found", resource_type="Service", resource_id=data.service_id
        )
    session = await CreateServiceSessionUseCase(session_repo).execute(
        session_id=SessionId(generate_cuid()),
        tenant_id=TenantId(tenant_id),
        service_id=ServiceId(data.service_id),
        provider_id=ProviderId(data.provider_id),
        member_id=EligibleMemberId(data.member_id),
        scheduled_at=scheduled_at,
        delivery_context=data.delivery_context,
        provider_affiliation_id=data.provider_affiliation_id,
        location=data.location,
        session_type=data.session_type,
        category=data.category,
        rate_ugx=data.rate_ugx,
        issue_topic=data.issue_topic,
        diagnosis_type_id=data.diagnosis_type_id,
        diagnosis_id=data.diagnosis_id,
        approved_by=data.approved_by,
        session_number=data.session_number,
        partner_name=data.partner_name,
        partner_relationship=data.partner_relationship,
        headcount=data.headcount,
        client_type=data.client_type,
        clinical_outcome=data.clinical_outcome,
    )
    await audit_change(session, audit_handler, current_user, request, tenant_id=tenant_id)
    return await _one(session, attribution_reader)


@router.post(
    "/{session_id}/complete",
    response_model=ServiceSessionCompleteResponse,
    summary="Complete a service session",
)
@transactional()
async def complete_service_session(
    request: Request,
    body: ServiceSessionCompleteRequest,
    current_user: TokenData = Depends(get_current_user),
    session: ServiceSessionEntity = Depends(get_service_session_for_current_tenant),
    session_repo: ServiceSessionRepository = Depends(get_service_session_repository),
    service_repo: ServiceRepository = Depends(get_service_repository),
    authorization_repo: AuthorizationRepository = Depends(get_authorization_repository),
    case_repo: CaseRepository = Depends(get_case_repository),
    member_repo: EligibleMemberRepository = Depends(get_eligible_member_repository),
    attribution_reader: SessionAttributionReader = Depends(get_session_attribution_reader),
    audit_handler=Depends(get_audit_event_handler),
    db: AsyncSession = Depends(get_db),
):
    """Complete a service session, drawing it down when a case is supplied."""
    use_case = TransitionUseCase(session_repo, "Session")
    session = await use_case.execute(
        session.id,
        ServiceSessionTransition.COMPLETE,
        duration=body.duration,
        notes=body.notes,
    )
    await audit_change(session, audit_handler, current_user, request)
    drawdown = await _draw_down(
        session,
        case_id=body.case_id,
        tenant_id=current_user.tenant_id,
        service_repo=service_repo,
        authorization_repo=authorization_repo,
        case_repo=case_repo,
        member_repo=member_repo,
    )
    return ServiceSessionCompleteResponse(
        session=await _one(session, attribution_reader), drawdown=drawdown
    )


async def _draw_down(
    session: ServiceSessionEntity,
    *,
    case_id: str | None,
    tenant_id: str,
    service_repo: ServiceRepository,
    authorization_repo: AuthorizationRepository,
    case_repo: CaseRepository,
    member_repo: EligibleMemberRepository,
) -> SessionDrawdownResponse:
    """Consume one authorized session, when the caller named the case."""
    if not case_id:
        return SessionDrawdownResponse(
            consumed=False, reason="No case supplied; authorization untouched"
        )
    # The case is supplied by the caller, so it has to be checked rather than
    # trusted: without this, naming another client's case would spend that
    # client's entitlement. Both sides carry an employer-side client_id, so
    # this compares them without touching the pseudonymous subject link.
    case = await case_repo.get_by_id(CaseId(case_id))
    if case is None or case.tenant_id.value != tenant_id:
        return SessionDrawdownResponse(consumed=False, reason="Case not found")
    member = await member_repo.get_by_id(session.member_id)
    if member is None or member.client_id != case.client_id:
        return SessionDrawdownResponse(
            consumed=False, reason="Case belongs to a different client than this session"
        )
    service = await service_repo.get_by_id(session.service_id)
    result = await ConsumeAuthorizationForSessionUseCase(authorization_repo).execute(
        tenant_id=TenantId(tenant_id),
        case_id=CaseId(case_id),
        service_category=service.category if service else None,
    )
    if not result.consumed:
        return SessionDrawdownResponse(consumed=False, reason=result.reason)
    return SessionDrawdownResponse(
        consumed=True,
        authorization_id=result.authorization.id.value,
        sessions_remaining=result.authorization.sessions_remaining,
    )


@router.post(
    "/{session_id}/cancel",
    response_model=ServiceSessionResponse,
    summary="Cancel a service session",
)
@transactional()
async def cancel_service_session(
    request: Request,
    body: ServiceSessionCancelRequest,
    current_user: TokenData = Depends(get_current_user),
    session: ServiceSessionEntity = Depends(get_service_session_for_current_tenant),
    session_repo: ServiceSessionRepository = Depends(get_service_session_repository),
    attribution_reader: SessionAttributionReader = Depends(get_session_attribution_reader),
    audit_handler=Depends(get_audit_event_handler),
    db: AsyncSession = Depends(get_db),
):
    """Cancel a service session."""
    use_case = TransitionUseCase(session_repo, "Session")
    session = await use_case.execute(
        session.id, ServiceSessionTransition.CANCEL, reason=body.reason
    )
    await audit_change(session, audit_handler, current_user, request)
    return await _one(session, attribution_reader)


@router.post(
    "/{session_id}/reschedule",
    response_model=ServiceSessionResponse,
    dependencies=[Depends(require_not_viewer)],
    summary="Reschedule a service session",
)
@transactional()
async def reschedule_service_session(
    request: Request,
    body: ServiceSessionRescheduleRequest,
    current_user: TokenData = Depends(get_current_user),
    session: ServiceSessionEntity = Depends(get_service_session_for_current_tenant),
    session_repo: ServiceSessionRepository = Depends(get_service_session_repository),
    provider_repo: ProviderRepository = Depends(get_provider_repository),
    affiliation_repo: ProviderAffiliationRepository = Depends(get_provider_affiliation_repository),
    organisation_repo: ProviderOrganisationRepository = Depends(
        get_provider_organisation_repository
    ),
    attribution_reader: SessionAttributionReader = Depends(get_session_attribution_reader),
    audit_handler=Depends(get_audit_event_handler),
    db: AsyncSession = Depends(get_db),
):
    """Reschedule a service session, re-checking eligibility for the new date.

    The whole gate is reapplied, not just the practitioner's half: an
    affiliation valid at the original time need not cover the new one.
    """
    new_scheduled_at = ensure_utc(body.new_scheduled_at)
    _reject_unknown_context(session.delivery_context)
    await _require_bookable(
        provider_repo,
        session.tenant_id,
        session.provider_id,
        new_scheduled_at,
        delivery_context=session.delivery_context,
        affiliation_id=session.provider_affiliation_id,
        affiliation_repo=affiliation_repo,
        organisation_repo=organisation_repo,
    )
    use_case = TransitionUseCase(session_repo, "Session")
    session = await use_case.execute(
        session.id,
        ServiceSessionTransition.RESCHEDULE,
        new_scheduled_at=new_scheduled_at,
    )
    await audit_change(session, audit_handler, current_user, request)
    return await _one(session, attribution_reader)


@router.post(
    "/{session_id}/no-show",
    response_model=ServiceSessionResponse,
    summary="Mark a service session as no-show",
)
@transactional()
async def mark_no_show_service_session(
    request: Request,
    current_user: TokenData = Depends(get_current_user),
    session: ServiceSessionEntity = Depends(get_service_session_for_current_tenant),
    session_repo: ServiceSessionRepository = Depends(get_service_session_repository),
    attribution_reader: SessionAttributionReader = Depends(get_session_attribution_reader),
    audit_handler=Depends(get_audit_event_handler),
    db: AsyncSession = Depends(get_db),
):
    """Mark a service session as no-show."""
    use_case = TransitionUseCase(session_repo, "Session")
    session = await use_case.execute(session.id, ServiceSessionTransition.MARK_NO_SHOW)
    await audit_change(session, audit_handler, current_user, request)
    return await _one(session, attribution_reader)


@router.patch(
    "/{session_id}",
    response_model=ServiceSessionResponse,
    summary="Update service session information",
)
@transactional()
async def update_service_session(
    data: ServiceSessionUpdate,
    request: Request,
    current_user: TokenData = Depends(get_current_user),
    session: ServiceSessionEntity = Depends(get_service_session_for_current_tenant),
    session_repo: ServiceSessionRepository = Depends(get_service_session_repository),
    attribution_reader: SessionAttributionReader = Depends(get_session_attribution_reader),
    audit_handler=Depends(get_audit_event_handler),
    db: AsyncSession = Depends(get_db),
):
    """Update service session information."""
    session = await UpdateServiceSessionUseCase(session_repo).execute(
        session.id,
        location=data.location,
        notes=data.notes,
        session_type=data.session_type,
        category=data.category,
        headcount=data.headcount,
        rate_ugx=data.rate_ugx,
        issue_topic=data.issue_topic,
        diagnosis_type_id=data.diagnosis_type_id,
        diagnosis_id=data.diagnosis_id,
        approved_by=data.approved_by,
        partner_name=data.partner_name,
        partner_relationship=data.partner_relationship,
        client_type=data.client_type,
        clinical_outcome=data.clinical_outcome,
    )
    await audit_change(session, audit_handler, current_user, request)
    return await _one(session, attribution_reader)


@router.patch(
    "/{session_id}/feedback",
    response_model=ServiceSessionResponse,
    summary="Update service session feedback",
)
@transactional()
async def update_service_session_feedback(
    request: Request,
    body: ServiceSessionUpdateFeedback,
    current_user: TokenData = Depends(get_current_user),
    session: ServiceSessionEntity = Depends(get_service_session_for_current_tenant),
    session_repo: ServiceSessionRepository = Depends(get_service_session_repository),
    attribution_reader: SessionAttributionReader = Depends(get_session_attribution_reader),
    audit_handler=Depends(get_audit_event_handler),
    db: AsyncSession = Depends(get_db),
):
    """Update service session feedback."""
    use_case = TransitionUseCase(session_repo, "Session")
    session = await use_case.execute(
        session.id,
        ServiceSessionTransition.UPDATE_FEEDBACK,
        feedback=body.feedback,
    )
    await audit_change(session, audit_handler, current_user, request)
    return await _one(session, attribution_reader)


@router.post(
    "/{session_id}/archive",
    response_model=ServiceSessionResponse,
    summary="Archive a service session",
)
@transactional()
async def archive_service_session(
    request: Request,
    current_user: TokenData = Depends(get_current_user),
    session: ServiceSessionEntity = Depends(get_service_session_for_current_tenant),
    session_repo: ServiceSessionRepository = Depends(get_service_session_repository),
    attribution_reader: SessionAttributionReader = Depends(get_session_attribution_reader),
    audit_handler=Depends(get_audit_event_handler),
    db: AsyncSession = Depends(get_db),
):
    """Archive a service session."""
    use_case = TransitionUseCase(session_repo, "Session")
    session = await use_case.execute(session.id, ServiceSessionTransition.ARCHIVE)
    await audit_change(session, audit_handler, current_user, request)
    return await _one(session, attribution_reader)


@router.post(
    "/{session_id}/restore",
    response_model=ServiceSessionResponse,
    summary="Restore a service session",
)
@transactional()
async def restore_service_session(
    request: Request,
    current_user: TokenData = Depends(get_current_user),
    session: ServiceSessionEntity = Depends(get_service_session_for_current_tenant),
    session_repo: ServiceSessionRepository = Depends(get_service_session_repository),
    attribution_reader: SessionAttributionReader = Depends(get_session_attribution_reader),
    audit_handler=Depends(get_audit_event_handler),
    db: AsyncSession = Depends(get_db),
):
    """Restore an archived service session."""
    use_case = TransitionUseCase(session_repo, "Session")
    session = await use_case.execute(session.id, ServiceSessionTransition.RESTORE)
    await audit_change(session, audit_handler, current_user, request)
    return await _one(session, attribution_reader)


# ==================== QUERIES (Direct Repository) ====================


@router.get(
    "/",
    response_model=ServiceSessionListResponse,
    summary="List service sessions with filtering and pagination",
)
@readonly()
async def list_service_sessions(
    tenant_id: str = Query(..., description="Tenant identifier"),
    current_user: TokenData = Depends(require_same_tenant),
    member_id: str | None = Query(None, description="Filter by member identifier"),
    provider_id: str | None = Query(None, description="Filter by provider identifier"),
    service_id: str | None = Query(None, description="Filter by service identifier"),
    status: SessionStatus | None = Query(None, description="Filter by session status"),
    scheduled_from: datetime | None = Query(
        None, description="Only sessions scheduled at or after this instant (ISO 8601)"
    ),
    scheduled_to: datetime | None = Query(
        None, description="Only sessions scheduled at or before this instant (ISO 8601)"
    ),
    pg: PageParams = Depends(pagination()),
    sort_by: str = Query("scheduled_at", description="Field to sort by"),
    sort_desc: bool = Query(True, description="Sort in descending order"),
    session_repo: ServiceSessionRepository = Depends(get_service_session_repository),
    attribution_reader: SessionAttributionReader = Depends(get_session_attribution_reader),
    db: AsyncSession = Depends(get_db),
):
    """List service sessions with filtering, searching, and pagination."""

    sessions = await session_repo.list_all(
        tenant_id=TenantId(tenant_id),
        member_id=EligibleMemberId(member_id) if member_id else None,
        provider_id=ProviderId(provider_id) if provider_id else None,
        service_id=ServiceId(service_id) if service_id else None,
        status=status,
        scheduled_from=scheduled_from,
        scheduled_to=scheduled_to,
        limit=pg.limit,
        offset=pg.offset,
        sort_by=sort_by,
        sort_desc=sort_desc,
    )

    total = await session_repo.count(
        tenant_id=TenantId(tenant_id),
        member_id=EligibleMemberId(member_id) if member_id else None,
        provider_id=ProviderId(provider_id) if provider_id else None,
        service_id=ServiceId(service_id) if service_id else None,
        status=status,
        scheduled_from=scheduled_from,
        scheduled_to=scheduled_to,
    )

    return ServiceSessionListResponse(
        items=await _many(sessions, attribution_reader),
        total=total,
        page=pg.page,
        limit=pg.limit,
        has_more=(pg.offset + pg.limit) < total,
    )


@router.get(
    "/{session_id}",
    response_model=ServiceSessionResponse,
    summary="Get service session by ID",
)
@readonly()
async def get_service_session(
    session: ServiceSessionEntity = Depends(get_service_session_for_current_tenant),
    attribution_reader: SessionAttributionReader = Depends(get_session_attribution_reader),
    db: AsyncSession = Depends(get_db),
):
    """Get service session by ID."""
    return await _one(session, attribution_reader)


@router.get(
    "/member/{member_id}",
    response_model=list[ServiceSessionResponse],
    summary="Get all sessions for a member",
)
@readonly()
async def get_sessions_by_member(
    member_id: str,
    tenant_id: str = Query(..., description="Tenant identifier"),
    current_user: TokenData = Depends(require_same_tenant),
    session_repo: ServiceSessionRepository = Depends(get_service_session_repository),
    attribution_reader: SessionAttributionReader = Depends(get_session_attribution_reader),
    db: AsyncSession = Depends(get_db),
):
    """Get all sessions for a member."""
    sessions = await GetServiceSessionUseCase(session_repo).execute_by_member(
        TenantId(tenant_id), EligibleMemberId(member_id)
    )
    return await _many(sessions, attribution_reader)


@router.get(
    "/provider/{provider_id}",
    response_model=list[ServiceSessionResponse],
    summary="Get all sessions for a provider",
)
@readonly()
async def get_sessions_by_provider(
    provider_id: str,
    tenant_id: str = Query(..., description="Tenant identifier"),
    current_user: TokenData = Depends(require_same_tenant),
    session_repo: ServiceSessionRepository = Depends(get_service_session_repository),
    attribution_reader: SessionAttributionReader = Depends(get_session_attribution_reader),
    db: AsyncSession = Depends(get_db),
):
    """Get all sessions for a provider."""
    sessions = await GetServiceSessionUseCase(session_repo).execute_by_provider(
        TenantId(tenant_id), ProviderId(provider_id)
    )
    return await _many(sessions, attribution_reader)


@router.get(
    "/service/{service_id}",
    response_model=list[ServiceSessionResponse],
    summary="Get all sessions for a service",
)
@readonly()
async def get_sessions_by_service(
    service_id: str,
    tenant_id: str = Query(..., description="Tenant identifier"),
    current_user: TokenData = Depends(require_same_tenant),
    session_repo: ServiceSessionRepository = Depends(get_service_session_repository),
    attribution_reader: SessionAttributionReader = Depends(get_session_attribution_reader),
    db: AsyncSession = Depends(get_db),
):
    """Get all sessions for a service."""
    sessions = await GetServiceSessionUseCase(session_repo).execute_by_service(
        TenantId(tenant_id), ServiceId(service_id)
    )
    return await _many(sessions, attribution_reader)
