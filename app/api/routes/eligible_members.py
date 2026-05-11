"""Eligible-member routes (Phase 5A #5A.1).

Employer-side routes for managing the EAP eligibility roster. Clinical-scope
endpoints (subject lookup, continuity metadata) live separately and will gain
their scope guard in 5A.2.
"""

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import (
    get_audit_event_handler,
    get_clinical_subject_repository,
    get_eligible_member_clinical_link_repository,
    get_eligible_member_repository,
)
from app.api.schemas.eligible_member_schemas import (
    EligibleMemberEnrol,
    EligibleMemberResponse,
)
from app.application.use_cases.eligible_member_use_cases import (
    EnrolEligibleMemberUseCase,
)
from app.core.authorization import require_same_tenant
from app.core.config import settings
from app.core.database import get_db
from app.core.security import TokenData, get_current_user
from app.domain.entities.eligible_member import EligibleMember
from app.domain.repositories.eligible_member_repository import (
    ClinicalSubjectRepository,
    EligibleMemberClinicalLinkRepository,
    EligibleMemberRepository,
)
from app.domain.value_objects.core import (
    ClientId,
    Email,
    EligibleMemberId,
    TenantId,
    UserId,
)
from app.shared.decorators import readonly, transactional
from app.shared.utils.route_audit_helper import audit_entity_operation

router = APIRouter(tags=["eligible-members"])


def _to_response(m: EligibleMember) -> EligibleMemberResponse:
    return EligibleMemberResponse(
        id=m.id.value,
        tenant_id=m.tenant_id.value,
        client_id=m.client_id.value,
        employer_member_id=m.employer_member_id,
        relation=m.relation,
        status=m.status,
        primary_employee_member_id=(
            m.primary_employee_member_id.value
            if m.primary_employee_member_id
            else None
        ),
        coverage_start=m.coverage_start,
        coverage_end=m.coverage_end,
        display_label=m.display_label,
        last_imported_at=m.last_imported_at,
        suspended_at=m.suspended_at,
        terminated_at=m.terminated_at,
        created_at=m.created_at,
        updated_at=m.updated_at,
    )


def _tenant_pseudonym_secret(tenant_id: str) -> str:
    base = getattr(settings, "PSEUDONYM_TENANT_SECRET", None) or getattr(
        settings, "SECRET_KEY", None
    ) or "evexia-default-pseudonym-key-please-rotate"
    return f"{base}:{tenant_id}"


@router.post(
    "/eligible-members",
    response_model=EligibleMemberResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Enrol an eligible member (auto-creates the linked clinical subject)",
)
@transactional()
async def enrol_eligible_member(
    data: EligibleMemberEnrol,
    request: Request,
    current_user: TokenData = Depends(get_current_user),
    member_repo: EligibleMemberRepository = Depends(get_eligible_member_repository),
    subject_repo: ClinicalSubjectRepository = Depends(
        get_clinical_subject_repository
    ),
    link_repo: EligibleMemberClinicalLinkRepository = Depends(
        get_eligible_member_clinical_link_repository
    ),
    audit_handler=Depends(get_audit_event_handler),
    db: AsyncSession = Depends(get_db),
):
    use_case = EnrolEligibleMemberUseCase(member_repo, subject_repo, link_repo)
    member, _ = await use_case.execute(
        tenant_id=TenantId(current_user.tenant_id),
        client_id=ClientId(data.client_id),
        employer_member_id=data.employer_member_id,
        relation=data.relation,
        tenant_secret=_tenant_pseudonym_secret(current_user.tenant_id),
        created_by=UserId(current_user.user_id),
        primary_employee_member_id=(
            EligibleMemberId(data.primary_employee_member_id)
            if data.primary_employee_member_id
            else None
        ),
        coverage_start=data.coverage_start,
        coverage_end=data.coverage_end,
        work_email=Email(str(data.work_email)) if data.work_email else None,
        personal_email=(
            Email(str(data.personal_email)) if data.personal_email else None
        ),
        display_label=data.display_label,
    )
    await audit_entity_operation(
        entity=member,
        audit_handler=audit_handler,
        tenant_id=member.tenant_id,
        user_id=current_user.user_id,
        request=request,
    )
    return _to_response(member)


@router.get(
    "/eligible-members",
    response_model=list[EligibleMemberResponse],
    summary="List eligible members for a client",
)
@readonly()
async def list_eligible_members(
    client_id: str,
    current_user: TokenData = Depends(get_current_user),
    member_repo: EligibleMemberRepository = Depends(get_eligible_member_repository),
    db: AsyncSession = Depends(get_db),
):
    members = await member_repo.list_for_client(
        TenantId(current_user.tenant_id), ClientId(client_id)
    )
    return [_to_response(m) for m in members]


@router.get(
    "/eligible-members/{member_id}",
    response_model=EligibleMemberResponse,
    summary="Get one eligible member",
)
@readonly()
async def get_eligible_member(
    member_id: str,
    current_user: TokenData = Depends(get_current_user),
    member_repo: EligibleMemberRepository = Depends(get_eligible_member_repository),
    db: AsyncSession = Depends(get_db),
):
    m = await member_repo.get_by_id(EligibleMemberId(member_id))
    if m is None:
        raise HTTPException(status_code=404, detail="Eligible member not found")
    require_same_tenant(current_user, m.tenant_id.value)
    return _to_response(m)
