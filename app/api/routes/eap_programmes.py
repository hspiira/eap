"""EAP programme + Authorization routes — CLINICAL-scope only."""

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import (
    get_audit_event_handler,
    get_authorization_repository,
    get_case_repository,
    get_eap_programme_repository,
)
from app.api.schemas.eap_programme_schemas import (
    AuthorizationResponse,
    AuthorizeCaseRequest,
    CreateEAPProgrammeRequest,
    EAPProgrammeResponse,
    GrantExtensionRequest,
    RequestExtensionRequest,
)
from app.application.use_cases.eap_programme_use_cases import (
    AuthorizeCaseUseCase,
    ConsumeAuthorizationSessionUseCase,
    CreateEAPProgrammeUseCase,
    GrantAuthorizationExtensionUseCase,
    RequestAuthorizationExtensionUseCase,
)
from app.core.authorization import require_clinical_scope, require_same_tenant
from app.core.database import get_db
from app.core.security import TokenData
from app.domain.entities.authorization import Authorization
from app.domain.entities.eap_programme import EAPProgramme
from app.domain.repositories.case_repository import CaseRepository
from app.domain.repositories.eap_programme_repository import (
    AuthorizationRepository,
    EAPProgrammeRepository,
)
from app.domain.value_objects.core import (
    AuthorizationId,
    CaseId,
    ContractId,
    EAPProgrammeId,
    TenantId,
    UserId,
)
from app.domain.value_objects.programme import ProgrammeSessionCap
from app.shared.decorators import readonly, transactional
from app.shared.utils.generators import generate_cuid
from app.shared.utils.route_audit_helper import audit_change

router = APIRouter(tags=["eap-programmes"])


def _to_programme(p: EAPProgramme) -> EAPProgrammeResponse:
    return EAPProgrammeResponse(
        id=p.id.value,
        tenant_id=p.tenant_id.value,
        contract_id=p.contract_id.value,
        name=p.name,
        effective_from=p.effective_from,
        effective_until=p.effective_until,
        geographic_scope=p.geographic_scope,
        description=p.description,
        eligible_dependent_relations=list(p.eligible_dependent_relations),
        caps=[c.as_dict() for c in p.caps],
        is_active=p.is_active,
        created_at=p.created_at,
        updated_at=p.updated_at,
    )


def _to_authorization(a: Authorization) -> AuthorizationResponse:
    return AuthorizationResponse(
        id=a.id.value,
        tenant_id=a.tenant_id.value,
        case_id=a.case_id.value,
        clinical_subject_id=a.clinical_subject_id.value,
        programme_id=a.programme_id.value,
        service_category=a.service_category,
        sessions_granted=a.sessions_granted,
        sessions_used=a.sessions_used,
        sessions_remaining=a.sessions_remaining,
        status=a.status,
        granted_at=a.granted_at,
        expires_on=a.expires_on,
        extension_requested_sessions=a.extension_requested_sessions,
        extended_at=a.extended_at,
        closed_at=a.closed_at,
        created_at=a.created_at,
        updated_at=a.updated_at,
    )


@router.post(
    "/eap-programmes",
    response_model=EAPProgrammeResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create an EAP programme attached to a contract",
)
@transactional()
async def create_programme(
    data: CreateEAPProgrammeRequest,
    request: Request,
    current_user: TokenData = Depends(require_clinical_scope),
    repo: EAPProgrammeRepository = Depends(get_eap_programme_repository),
    audit_handler=Depends(get_audit_event_handler),
    db: AsyncSession = Depends(get_db),
):
    use_case = CreateEAPProgrammeUseCase(repo)
    programme = await use_case.execute(
        programme_id=EAPProgrammeId(generate_cuid()),
        tenant_id=TenantId(current_user.tenant_id),
        contract_id=ContractId(data.contract_id),
        name=data.name,
        effective_from=data.effective_from,
        effective_until=data.effective_until,
        caps=tuple(
            ProgrammeSessionCap(
                service_category=c.service_category,
                per_issue_per_year=c.per_issue_per_year,
                per_year=c.per_year,
                per_household_per_year=c.per_household_per_year,
            )
            for c in data.caps
        ),
        eligible_dependent_relations=tuple(data.eligible_dependent_relations),
        geographic_scope=data.geographic_scope,
        description=data.description,
        created_by=UserId(current_user.user_id),
    )
    await audit_change(programme, audit_handler, current_user, request)
    return _to_programme(programme)


@router.get(
    "/eap-programmes",
    response_model=list[EAPProgrammeResponse],
    summary="List EAP programmes for the current tenant",
)
@readonly()
async def list_programmes(
    current_user: TokenData = Depends(require_clinical_scope),
    repo: EAPProgrammeRepository = Depends(get_eap_programme_repository),
    db: AsyncSession = Depends(get_db),
):
    rows = await repo.list_for_tenant(TenantId(current_user.tenant_id))
    return [_to_programme(p) for p in rows]


@router.get(
    "/eap-programmes/{programme_id}",
    response_model=EAPProgrammeResponse,
    summary="Get one EAP programme",
)
@readonly()
async def get_programme(
    programme_id: str,
    current_user: TokenData = Depends(require_clinical_scope),
    repo: EAPProgrammeRepository = Depends(get_eap_programme_repository),
    db: AsyncSession = Depends(get_db),
):
    p = await repo.get_by_id(EAPProgrammeId(programme_id))
    if p is None:
        raise HTTPException(status_code=404, detail="Programme not found")
    require_same_tenant(current_user, p.tenant_id.value)
    return _to_programme(p)


@router.post(
    "/cases/{case_id}/authorize",
    response_model=AuthorizationResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Authorize a case from a programme cap",
)
@transactional()
async def authorize_case(
    case_id: str,
    data: AuthorizeCaseRequest,
    request: Request,
    current_user: TokenData = Depends(require_clinical_scope),
    programme_repo: EAPProgrammeRepository = Depends(
        get_eap_programme_repository
    ),
    auth_repo: AuthorizationRepository = Depends(get_authorization_repository),
    case_repo: CaseRepository = Depends(get_case_repository),
    audit_handler=Depends(get_audit_event_handler),
    db: AsyncSession = Depends(get_db),
):
    use_case = AuthorizeCaseUseCase(programme_repo, auth_repo, case_repo)
    auth = await use_case.execute(
        case_id=CaseId(case_id),
        programme_id=EAPProgrammeId(data.programme_id),
        service_category=data.service_category,
        expires_on=data.expires_on,
    )
    await audit_change(auth, audit_handler, current_user, request)
    return _to_authorization(auth)


@router.post(
    "/authorizations/{authorization_id}/consume",
    response_model=AuthorizationResponse,
    summary="Decrement an authorization by one session",
)
@transactional()
async def consume_session(
    authorization_id: str,
    request: Request,
    current_user: TokenData = Depends(require_clinical_scope),
    repo: AuthorizationRepository = Depends(get_authorization_repository),
    audit_handler=Depends(get_audit_event_handler),
    db: AsyncSession = Depends(get_db),
):
    auth = await ConsumeAuthorizationSessionUseCase(repo).execute(
        AuthorizationId(authorization_id)
    )
    await audit_change(auth, audit_handler, current_user, request)
    return _to_authorization(auth)


@router.post(
    "/authorizations/{authorization_id}/request-extension",
    response_model=AuthorizationResponse,
    summary="Request an extension to the session cap",
)
@transactional()
async def request_extension(
    authorization_id: str,
    data: RequestExtensionRequest,
    request: Request,
    current_user: TokenData = Depends(require_clinical_scope),
    repo: AuthorizationRepository = Depends(get_authorization_repository),
    audit_handler=Depends(get_audit_event_handler),
    db: AsyncSession = Depends(get_db),
):
    auth = await RequestAuthorizationExtensionUseCase(repo).execute(
        authorization_id=AuthorizationId(authorization_id),
        additional_sessions=data.additional_sessions,
        requested_by=UserId(current_user.user_id),
    )
    await audit_change(auth, audit_handler, current_user, request)
    return _to_authorization(auth)


@router.post(
    "/authorizations/{authorization_id}/grant-extension",
    response_model=AuthorizationResponse,
    summary="Grant a pending extension (clinician + admin two-person sign-off)",
)
@transactional()
async def grant_extension(
    authorization_id: str,
    data: GrantExtensionRequest,
    request: Request,
    current_user: TokenData = Depends(require_clinical_scope),
    repo: AuthorizationRepository = Depends(get_authorization_repository),
    audit_handler=Depends(get_audit_event_handler),
    db: AsyncSession = Depends(get_db),
):
    auth = await GrantAuthorizationExtensionUseCase(repo).execute(
        authorization_id=AuthorizationId(authorization_id),
        clinician_signoff=UserId(data.clinician_signoff_user_id),
        admin_signoff=UserId(data.admin_signoff_user_id),
    )
    await audit_change(auth, audit_handler, current_user, request)
    return _to_authorization(auth)
