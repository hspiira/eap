"""Clinical case routes, CLINICAL-scope only."""

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import (
    get_audit_event_handler,
    get_case_repository,
    get_clinical_note_repository,
    get_eligible_member_clinical_link_repository,
    get_user_repository,
)
from app.api.schemas.case_schemas import (
    AdvanceCaseRequest,
    AssignCounsellorRequest,
    CaseResponse,
    CloseCaseRequest,
    OpenCaseRequest,
    ReferOutCaseRequest,
)
from app.application.use_cases.case_use_cases import (
    AdvanceCaseStatusUseCase,
    AssignCounsellorUseCase,
    CloseCaseUseCase,
    OpenCaseUseCase,
    ReferOutCaseUseCase,
)
from app.core.authorization import require_clinical_scope, require_same_tenant
from app.core.database import get_db
from app.core.security import TokenData
from app.domain.entities.case import Case
from app.domain.repositories.case_repository import CaseRepository
from app.domain.repositories.clinical_note_repository import ClinicalNoteRepository
from app.domain.repositories.eligible_member_repository import (
    EligibleMemberClinicalLinkRepository,
)
from app.domain.repositories.user_repository import UserRepository
from app.domain.value_objects.core import (
    CaseId,
    ClientId,
    EligibleMemberId,
    PersonId,
    TenantId,
    UserId,
)
from app.shared.decorators import readonly, transactional
from app.shared.utils.generators import generate_cuid
from app.shared.utils.route_audit_helper import audit_change

router = APIRouter(tags=["cases"])


def _to_response(c: Case) -> CaseResponse:
    return CaseResponse(
        id=c.id.value,
        tenant_id=c.tenant_id.value,
        clinical_subject_id=c.clinical_subject_id.value,
        client_id=c.client_id.value,
        presenting_problem=c.presenting_problem,
        referral_source=c.referral_source,
        status=c.status,
        opened_at=c.opened_at,
        assigned_counsellor_id=(
            c.assigned_counsellor_id.value if c.assigned_counsellor_id else None
        ),
        authorization_id=(c.authorization_id.value if c.authorization_id else None),
        referred_by_user_id=(c.referred_by_user_id.value if c.referred_by_user_id else None),
        referral_notes=c.referral_notes,
        closed_at=c.closed_at,
        closure_reason=c.closure_reason,
        closure_summary_note_id=c.closure_summary_note_id,
        intake_screener_admin_ids=list(c.intake_screener_admin_ids),
        closure_screener_admin_ids=list(c.closure_screener_admin_ids),
        created_at=c.created_at,
        updated_at=c.updated_at,
    )


@router.post(
    "/cases",
    response_model=CaseResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Open a clinical case (resolves the eligible member to a clinical subject)",
)
@transactional()
async def open_case(
    data: OpenCaseRequest,
    request: Request,
    current_user: TokenData = Depends(require_clinical_scope),
    case_repo: CaseRepository = Depends(get_case_repository),
    link_repo: EligibleMemberClinicalLinkRepository = Depends(
        get_eligible_member_clinical_link_repository
    ),
    audit_handler=Depends(get_audit_event_handler),
    db: AsyncSession = Depends(get_db),
):
    use_case = OpenCaseUseCase(case_repo, link_repo)
    case = await use_case.execute(
        case_id=CaseId(generate_cuid()),
        tenant_id=TenantId(current_user.tenant_id),
        client_id=ClientId(data.client_id),
        member_id=EligibleMemberId(data.member_id),
        presenting_problem=data.presenting_problem,
        referral_source=data.referral_source,
        opened_by=UserId(current_user.user_id),
        referral_notes=data.referral_notes,
    )
    await audit_change(case, audit_handler, current_user, request)
    return _to_response(case)


@router.get(
    "/cases",
    response_model=list[CaseResponse],
    summary="List cases for the current tenant",
)
@readonly()
async def list_cases(
    current_user: TokenData = Depends(require_clinical_scope),
    case_repo: CaseRepository = Depends(get_case_repository),
    db: AsyncSession = Depends(get_db),
):
    cases = await case_repo.list_for_tenant(TenantId(current_user.tenant_id))
    return [_to_response(c) for c in cases]


@router.get(
    "/cases/{case_id}",
    response_model=CaseResponse,
    summary="Get one case",
)
@readonly()
async def get_case(
    case_id: str,
    current_user: TokenData = Depends(require_clinical_scope),
    case_repo: CaseRepository = Depends(get_case_repository),
    db: AsyncSession = Depends(get_db),
):
    case = await case_repo.get_by_id(CaseId(case_id))
    if case is None:
        raise HTTPException(status_code=404, detail="Case not found")
    require_same_tenant(current_user, case.tenant_id.value)
    return _to_response(case)


@router.post(
    "/cases/{case_id}/assign-counsellor",
    response_model=CaseResponse,
    summary="Assign a counsellor to the case",
)
@transactional()
async def assign_counsellor(
    case_id: str,
    data: AssignCounsellorRequest,
    request: Request,
    current_user: TokenData = Depends(require_clinical_scope),
    case_repo: CaseRepository = Depends(get_case_repository),
    user_repo: UserRepository = Depends(get_user_repository),
    audit_handler=Depends(get_audit_event_handler),
    db: AsyncSession = Depends(get_db),
):
    case = await AssignCounsellorUseCase(case_repo, user_repo).execute(
        case_id=CaseId(case_id),
        counsellor_id=PersonId(data.counsellor_id),
        tenant_id=TenantId(current_user.tenant_id),
    )
    await audit_change(case, audit_handler, current_user, request)
    return _to_response(case)


@router.post(
    "/cases/{case_id}/advance",
    response_model=CaseResponse,
    summary="Advance the case status (Intake → Assessment → Active)",
)
@transactional()
async def advance_case(
    case_id: str,
    data: AdvanceCaseRequest,
    request: Request,
    current_user: TokenData = Depends(require_clinical_scope),
    case_repo: CaseRepository = Depends(get_case_repository),
    audit_handler=Depends(get_audit_event_handler),
    db: AsyncSession = Depends(get_db),
):
    case = await AdvanceCaseStatusUseCase(case_repo).execute(
        case_id=CaseId(case_id), target=data.target
    )
    await audit_change(case, audit_handler, current_user, request)
    return _to_response(case)


@router.post(
    "/cases/{case_id}/close",
    response_model=CaseResponse,
    summary="Close the case",
)
@transactional()
async def close_case(
    case_id: str,
    data: CloseCaseRequest,
    request: Request,
    current_user: TokenData = Depends(require_clinical_scope),
    case_repo: CaseRepository = Depends(get_case_repository),
    audit_handler=Depends(get_audit_event_handler),
    db: AsyncSession = Depends(get_db),
):
    case = await CloseCaseUseCase(case_repo).execute(
        case_id=CaseId(case_id),
        reason=data.reason,
        closure_summary_note_id=data.closure_summary_note_id,
    )
    await audit_change(case, audit_handler, current_user, request)
    return _to_response(case)


@router.post(
    "/cases/{case_id}/refer-out",
    response_model=CaseResponse,
    summary="Refer the case out to an external provider",
)
@transactional()
async def refer_out_case(
    case_id: str,
    data: ReferOutCaseRequest,
    request: Request,
    current_user: TokenData = Depends(require_clinical_scope),
    case_repo: CaseRepository = Depends(get_case_repository),
    note_repo: ClinicalNoteRepository = Depends(get_clinical_note_repository),
    audit_handler=Depends(get_audit_event_handler),
    db: AsyncSession = Depends(get_db),
):
    case = await ReferOutCaseUseCase(case_repo, note_repo).execute(
        case_id=CaseId(case_id),
        notes=data.notes,
        referred_by=UserId(current_user.user_id),
        tenant_id=TenantId(current_user.tenant_id),
    )
    await audit_change(case, audit_handler, current_user, request)
    return _to_response(case)
