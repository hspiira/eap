"""Tenant-facing Members API.

Members are client-covered people, not providers or tenant staff. The existing
``eligible_members`` aggregate is the employer-side source of truth and is
also the only identity-bearing side allowed to link to clinical subjects.
"""

import csv
import io

from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from starlette.responses import StreamingResponse

from app.api.dependencies import (
    PageParams,
    get_audit_event_handler,
    get_client_repository,
    get_clinical_subject_repository,
    get_eligible_member_clinical_link_repository,
    get_eligible_member_repository,
    pagination,
)
from app.api.schemas.member_schemas import (
    MemberCreate,
    MemberDuplicateCandidate,
    MemberDuplicateListResponse,
    MemberListResponse,
    MemberResponse,
    MemberUpdate,
)
from app.application.use_cases.eligible_member_use_cases import EnrolEligibleMemberUseCase
from app.core.authorization import require_not_viewer
from app.core.security import TokenData, get_current_user
from app.domain.entities.eligible_member import EligibleMember
from app.domain.enums import EligibilityStatus, MemberRelation
from app.domain.repositories.client_repository import ClientRepository
from app.domain.repositories.eligible_member_repository import (
    ClinicalSubjectRepository,
    EligibleMemberClinicalLinkRepository,
    EligibleMemberRepository,
)
from app.domain.value_objects.core import (
    ClientId,
    EligibleMemberId,
    Email,
    TenantId,
    UserId,
)
from app.shared.decorators import readonly, transactional
from app.shared.utils.route_audit_helper import audit_change

router = APIRouter(prefix="/members", tags=["members"])


def _response(member: EligibleMember) -> MemberResponse:
    return MemberResponse(
        id=member.id.value,
        tenant_id=member.tenant_id.value,
        client_id=member.client_id.value,
        employer_member_id=member.employer_member_id,
        relation=member.relation,
        status=member.status,
        primary_employee_member_id=(
            member.primary_employee_member_id.value if member.primary_employee_member_id else None
        ),
        work_email=member.work_email.value if member.work_email else None,
        personal_email=member.personal_email.value if member.personal_email else None,
        display_label=member.display_label,
        date_of_birth=member.date_of_birth,
        gender=member.gender,
        phone=member.phone,
        last_imported_at=member.last_imported_at,
        suspended_at=member.suspended_at,
        terminated_at=member.terminated_at,
        created_at=member.created_at,
        updated_at=member.updated_at,
    )


async def _client_in_tenant(
    client_id: str,
    tenant_id: str,
    client_repo: ClientRepository,
) -> None:
    client = await client_repo.get_by_id(ClientId(client_id))
    if not client or client.tenant_id.value != tenant_id:
        raise HTTPException(status_code=404, detail="Client not found")


async def _validate_primary(
    member_repo: EligibleMemberRepository,
    primary_id: str | None,
    *,
    tenant_id: str,
    client_id: str,
) -> None:
    if primary_id is None:
        return
    primary = await member_repo.get_by_id(EligibleMemberId(primary_id))
    if (
        primary is None
        or primary.tenant_id.value != tenant_id
        or primary.client_id.value != client_id
        or primary.relation != MemberRelation.EMPLOYEE
    ):
        raise HTTPException(status_code=422, detail="Primary employee is not valid for this client")


@router.post("", response_model=MemberResponse, status_code=status.HTTP_201_CREATED)
@transactional()
async def create_member(
    data: MemberCreate,
    request: Request,
    current_user: TokenData = Depends(require_not_viewer),
    member_repo: EligibleMemberRepository = Depends(get_eligible_member_repository),
    client_repo: ClientRepository = Depends(get_client_repository),
    subject_repo: ClinicalSubjectRepository = Depends(get_clinical_subject_repository),
    link_repo: EligibleMemberClinicalLinkRepository = Depends(
        get_eligible_member_clinical_link_repository
    ),
    audit_handler=Depends(get_audit_event_handler),
):
    await _client_in_tenant(data.client_id, current_user.tenant_id, client_repo)
    await _validate_primary(
        member_repo,
        data.primary_employee_member_id,
        tenant_id=current_user.tenant_id,
        client_id=data.client_id,
    )
    use_case = EnrolEligibleMemberUseCase(member_repo, subject_repo, link_repo)
    member, _ = await use_case.execute(
        tenant_id=TenantId(current_user.tenant_id),
        client_id=ClientId(data.client_id),
        employer_member_id=data.employer_member_id,
        relation=data.relation,
        tenant_secret=_tenant_secret(current_user.tenant_id),
        created_by=UserId(current_user.user_id),
        primary_employee_member_id=(
            EligibleMemberId(data.primary_employee_member_id)
            if data.primary_employee_member_id
            else None
        ),
        work_email=Email(str(data.work_email)) if data.work_email else None,
        personal_email=Email(str(data.personal_email)) if data.personal_email else None,
        display_label=data.display_label,
        date_of_birth=data.date_of_birth,
        gender=data.gender,
        phone=data.phone,
    )
    await audit_change(member, audit_handler, current_user, request)
    return _response(member)


def _tenant_secret(tenant_id: str) -> str:
    from app.core.config import settings

    base = getattr(settings, "PSEUDONYM_TENANT_SECRET", None) or settings.SECRET_KEY
    return f"{base}:{tenant_id}"


@router.get("", response_model=MemberListResponse)
@readonly()
async def list_members(
    current_user: TokenData = Depends(get_current_user),
    client_id: str | None = Query(None),
    member_status: EligibilityStatus | None = Query(None, alias="status"),
    relation: MemberRelation | None = Query(None),
    search: str | None = Query(None),
    pg: PageParams = Depends(pagination()),
    sort_by: str = Query("created_at"),
    sort_desc: bool = Query(True),
    member_repo: EligibleMemberRepository = Depends(get_eligible_member_repository),
):
    client = ClientId(client_id) if client_id else None
    tenant = TenantId(current_user.tenant_id)
    items = await member_repo.list_all(
        tenant,
        client_id=client,
        status=member_status,
        relation=relation,
        search=search,
        limit=pg.limit,
        offset=pg.offset,
        sort_by=sort_by,
        sort_desc=sort_desc,
    )
    total = await member_repo.count(
        tenant,
        client_id=client,
        status=member_status,
        relation=relation,
        search=search,
    )
    return MemberListResponse(
        items=[_response(item) for item in items],
        total=total,
        page=pg.page,
        limit=pg.limit,
        has_more=pg.offset + pg.limit < total,
    )


@router.get("/export", response_class=StreamingResponse)
@readonly()
async def export_members(
    current_user: TokenData = Depends(get_current_user),
    member_ids: list[str] | None = Query(None),
    client_id: str | None = Query(None),
    member_status: EligibilityStatus | None = Query(None, alias="status"),
    relation: MemberRelation | None = Query(None),
    search: str | None = Query(None),
    member_repo: EligibleMemberRepository = Depends(get_eligible_member_repository),
):
    tenant = TenantId(current_user.tenant_id)
    if member_ids:
        members = []
        for raw_id in dict.fromkeys(member_ids):
            member = await member_repo.get_by_id(EligibleMemberId(raw_id))
            if member and member.tenant_id == tenant:
                members.append(member)
    else:
        members = await member_repo.list_all(
            tenant,
            client_id=ClientId(client_id) if client_id else None,
            status=member_status,
            relation=relation,
            search=search,
            limit=10_000,
            sort_by="created_at",
            sort_desc=True,
        )
    output = io.StringIO(newline="")
    fields = [
        "id",
        "client_id",
        "employer_member_id",
        "relation",
        "status",
        "display_label",
        "work_email",
        "personal_email",
        "primary_employee_member_id",
        "date_of_birth",
        "gender",
        "phone",
    ]
    writer = csv.DictWriter(output, fieldnames=fields)
    writer.writeheader()
    for member in members:
        item = _response(member)
        writer.writerow({field: getattr(item, field) for field in fields})
    return StreamingResponse(
        iter([output.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": 'attachment; filename="members.csv"'},
    )


@router.patch("/{member_id}", response_model=MemberResponse)
@transactional()
async def update_member(
    member_id: str,
    data: MemberUpdate,
    request: Request,
    current_user: TokenData = Depends(require_not_viewer),
    member_repo: EligibleMemberRepository = Depends(get_eligible_member_repository),
    client_repo: ClientRepository = Depends(get_client_repository),
    audit_handler=Depends(get_audit_event_handler),
):
    member = await member_repo.get_by_id(EligibleMemberId(member_id))
    if member is None or member.tenant_id.value != current_user.tenant_id:
        raise HTTPException(status_code=404, detail="Member not found")
    fields = data.model_fields_set
    relation = data.relation if "relation" in fields and data.relation else member.relation
    primary = (
        data.primary_employee_member_id
        if "primary_employee_member_id" in fields
        else (
            member.primary_employee_member_id.value if member.primary_employee_member_id else None
        )
    )
    await _validate_primary(
        member_repo,
        primary,
        tenant_id=current_user.tenant_id,
        client_id=member.client_id.value,
    )
    await _client_in_tenant(member.client_id.value, current_user.tenant_id, client_repo)
    member.update_roster_details(
        employer_member_id=(
            data.employer_member_id
            if "employer_member_id" in fields and data.employer_member_id is not None
            else member.employer_member_id
        ),
        relation=relation,
        primary_employee_member_id=EligibleMemberId(primary) if primary else None,
        coverage_start=member.coverage_start,
        coverage_end=member.coverage_end,
        work_email=(Email(str(data.work_email)) if data.work_email else None)
        if "work_email" in fields
        else member.work_email,
        personal_email=(Email(str(data.personal_email)) if data.personal_email else None)
        if "personal_email" in fields
        else member.personal_email,
        display_label=data.display_label if "display_label" in fields else member.display_label,
        date_of_birth=data.date_of_birth if "date_of_birth" in fields else member.date_of_birth,
        gender=data.gender if "gender" in fields else member.gender,
        phone=data.phone if "phone" in fields else member.phone,
    )
    await member_repo.save(member)
    await audit_change(member, audit_handler, current_user, request)
    return _response(member)


async def _transition_member(
    member_id: str,
    action: str,
    current_user: TokenData,
    member_repo: EligibleMemberRepository,
):
    member = await member_repo.get_by_id(EligibleMemberId(member_id))
    if member is None or member.tenant_id.value != current_user.tenant_id:
        raise HTTPException(status_code=404, detail="Member not found")
    getattr(member, action)()
    await member_repo.save(member)
    return member


@router.post("/{member_id}/suspend", response_model=MemberResponse)
@transactional()
async def suspend_member(
    member_id: str,
    request: Request,
    current_user: TokenData = Depends(require_not_viewer),
    member_repo: EligibleMemberRepository = Depends(get_eligible_member_repository),
    audit_handler=Depends(get_audit_event_handler),
):
    member = await _transition_member(member_id, "suspend", current_user, member_repo)
    await audit_change(member, audit_handler, current_user, request)
    return _response(member)


@router.post("/{member_id}/reinstate", response_model=MemberResponse)
@transactional()
async def reinstate_member(
    member_id: str,
    request: Request,
    current_user: TokenData = Depends(require_not_viewer),
    member_repo: EligibleMemberRepository = Depends(get_eligible_member_repository),
    audit_handler=Depends(get_audit_event_handler),
):
    member = await _transition_member(member_id, "reinstate", current_user, member_repo)
    await audit_change(member, audit_handler, current_user, request)
    return _response(member)


@router.post("/{member_id}/terminate", response_model=MemberResponse)
@transactional()
async def terminate_member(
    member_id: str,
    request: Request,
    current_user: TokenData = Depends(require_not_viewer),
    member_repo: EligibleMemberRepository = Depends(get_eligible_member_repository),
    audit_handler=Depends(get_audit_event_handler),
):
    member = await _transition_member(member_id, "terminate", current_user, member_repo)
    await audit_change(member, audit_handler, current_user, request)
    return _response(member)


@router.get("/duplicates", response_model=MemberDuplicateListResponse)
@readonly()
async def scan_member_duplicates(
    current_user: TokenData = Depends(get_current_user),
    client_id: str | None = Query(None),
    member_repo: EligibleMemberRepository = Depends(get_eligible_member_repository),
):
    members = await member_repo.list_all(
        TenantId(current_user.tenant_id),
        client_id=ClientId(client_id) if client_id else None,
        limit=10_000,
        sort_by="display_label",
        sort_desc=False,
    )
    groups: dict[str, list[EligibleMember]] = {}
    for member in members:
        keys = {member.employer_member_id.casefold()}
        if member.work_email:
            keys.add(f"email:{member.work_email.value.casefold()}")
        if member.personal_email:
            keys.add(f"email:{member.personal_email.value.casefold()}")
        if member.phone:
            keys.add(f"phone:{member.phone.casefold()}")
        if member.display_label:
            normalized_label = " ".join(member.display_label.casefold().split())
            keys.add(f"name:{normalized_label}")
        for key in keys:
            groups.setdefault(key, []).append(member)
    candidates: list[MemberDuplicateCandidate] = []
    seen: set[str] = set()
    for key, grouped in groups.items():
        unique = {member.id.value: member for member in grouped}
        if len(unique) < 2:
            continue
        for member in unique.values():
            if member.id.value in seen:
                continue
            matches = [m for m in unique.values() if m.id.value != member.id.value]
            fields = ["email"] if key.startswith("email:") else ["employer_member_id"]
            if key.startswith("phone:"):
                fields = ["phone"]
            if key.startswith("name:"):
                fields = ["display_label"]
            candidates.append(MemberDuplicateCandidate(member=_response(member), matched_on=fields))
            seen.add(member.id.value)
            if not matches:
                continue
    return MemberDuplicateListResponse(candidates=candidates)


@router.get("/{member_id}/beneficiaries", response_model=list[MemberResponse])
@readonly()
async def list_member_beneficiaries(
    member_id: str,
    current_user: TokenData = Depends(get_current_user),
    member_repo: EligibleMemberRepository = Depends(get_eligible_member_repository),
):
    member = await member_repo.get_by_id(EligibleMemberId(member_id))
    if member is None or member.tenant_id.value != current_user.tenant_id:
        raise HTTPException(status_code=404, detail="Member not found")
    if member.relation != MemberRelation.EMPLOYEE:
        return []
    beneficiaries = await member_repo.list_for_primary(
        TenantId(current_user.tenant_id),
        member.client_id,
        member.id,
    )
    return [_response(item) for item in beneficiaries]


@router.get("/{member_id}", response_model=MemberResponse)
@readonly()
async def get_member(
    member_id: str,
    current_user: TokenData = Depends(get_current_user),
    member_repo: EligibleMemberRepository = Depends(get_eligible_member_repository),
):
    member = await member_repo.get_by_id(EligibleMemberId(member_id))
    if member is None or member.tenant_id.value != current_user.tenant_id:
        raise HTTPException(status_code=404, detail="Member not found")
    return _response(member)
