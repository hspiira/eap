"""Tenant-facing Members API.

Members are client-covered people, not providers or tenant staff. The existing
``eligible_members`` aggregate is the employer-side source of truth and is
also the only identity-bearing side allowed to link to clinical subjects.
"""

import csv
import hashlib
import io
import logging
from collections.abc import Sequence
from copy import deepcopy
from dataclasses import dataclass
from typing import Any, Literal

from fastapi import (
    APIRouter,
    Depends,
    File,
    HTTPException,
    Query,
    Request,
    UploadFile,
    status,
)
from pydantic import ValidationError
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from starlette.responses import StreamingResponse

from app.api.dependencies import (
    PageParams,
    get_client_repository,
    get_clinical_subject_repository,
    get_eligible_member_clinical_link_repository,
    get_eligible_member_repository,
    get_member_import_repository,
    get_member_next_of_kin_repository,
    get_next_of_kin_relationship_repository,
    get_outbox_repository,
    get_service_session_repository,
    get_user_repository,
    pagination,
)
from app.api.routes.service_sessions import to_service_session_response
from app.api.schemas.member_schemas import (
    MemberAccountLinkRequest,
    MemberCreate,
    MemberDuplicateCandidate,
    MemberDuplicateListResponse,
    MemberDuplicateMember,
    MemberEmployment,
    MemberImportAbandonRequest,
    MemberImportApplyResponse,
    MemberImportBatchResponse,
    MemberImportRowDecisionRequest,
    MemberImportRowListResponse,
    MemberImportRowResponse,
    MemberListResponse,
    MemberMergeRequest,
    MemberMergeResponse,
    MemberNextOfKinCreate,
    MemberNextOfKinResponse,
    MemberNextOfKinUpdate,
    MemberResponse,
    MemberStatsResponse,
    MemberUpdate,
)
from app.api.schemas.service_session_schemas import ServiceSessionListResponse
from app.api.services.member_import import (
    MemberRowChecker,
    MemberRowImporter,
    MemberRowUpdater,
    RowCheck,
    build_row_entity,
    csv_row_from_entity,
    issue_member_code,
)
from app.application.use_cases.eligible_member_use_cases import EnrolEligibleMemberUseCase
from app.core.authorization import require_clinical_scope, require_not_viewer, require_tenant_role
from app.core.database import get_db
from app.core.query_metrics import measure_queries
from app.core.security import TokenData, get_current_user
from app.domain.entities.client import ClientEntity
from app.domain.entities.eligible_member import EligibleMember
from app.domain.entities.member_import import MemberImportBatchEntity, MemberImportRowEntity
from app.domain.entities.member_next_of_kin import MemberNextOfKin
from app.domain.enums import EligibilityStatus, MemberRelation, TenantRole
from app.domain.enums.provider_network import ImportBatchStatus
from app.domain.events import (
    EligibleMemberAccountLinked,
    EligibleMemberAccountUnlinked,
    EligibleMemberMerged,
    EligibleMemberMergedIntoMember,
    MemberNextOfKinCreated,
    MemberNextOfKinDeleted,
    MemberNextOfKinUpdated,
)
from app.domain.exceptions import DomainError, EvexiaException, NotFoundError
from app.domain.repositories.client_repository import ClientRepository
from app.domain.repositories.eligible_member_repository import (
    ClinicalSubjectRepository,
    EligibleMemberClinicalLinkRepository,
    EligibleMemberRepository,
)
from app.domain.repositories.member_import_repository import MemberImportRepository
from app.domain.repositories.member_next_of_kin_repository import MemberNextOfKinRepository
from app.domain.repositories.next_of_kin_relationship_repository import (
    NextOfKinRelationshipRepository,
)
from app.domain.repositories.outbox_repository import OutboxRepository
from app.domain.repositories.service_session_repository import ServiceSessionRepository
from app.domain.repositories.user_repository import UserRepository
from app.domain.value_objects.core import (
    ClientId,
    EligibleMemberId,
    Email,
    MemberImportBatchId,
    MemberImportRowId,
    MemberNextOfKinId,
    TenantId,
    UserId,
)
from app.domain.value_objects.staffing import EmploymentDetails
from app.shared.decorators import readonly, transactional
from app.shared.handlers.audit_event_handler import AuditEventHandler
from app.shared.utils.batched_commit import BatchedCommit
from app.shared.utils.datetime import utc_now
from app.shared.utils.errors import ErrorResponse
from app.shared.utils.generators import generate_cuid
from app.shared.utils.member_csv import MemberCsvRow, parse_member_csv
from app.shared.utils.route_audit_helper import audit_change

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/members", tags=["members"])


def _error_response(description: str) -> dict[str, Any]:
    """Describe one error status this router can return, for the OpenAPI schema."""
    return {"model": ErrorResponse, "description": description}


def _employment(data: MemberEmployment | None) -> EmploymentDetails | None:
    if data is None:
        return None
    return EmploymentDetails.build(**data.model_dump())


def _response(member: EligibleMember, client_name: str | None = None) -> MemberResponse:
    return MemberResponse(
        id=member.id.value,
        tenant_id=member.tenant_id.value,
        client_id=member.client_id.value,
        client_name=client_name,
        employer_member_id=member.employer_member_id,
        relation=member.relation,
        status=member.status,
        primary_employee_member_id=(
            member.primary_employee_member_id.value if member.primary_employee_member_id else None
        ),
        coverage_start=member.coverage_start,
        coverage_end=member.coverage_end,
        is_currently_eligible=member.is_currently_eligible(),
        work_email=member.work_email.value if member.work_email else None,
        personal_email=member.personal_email.value if member.personal_email else None,
        display_label=member.display_label,
        date_of_birth=member.date_of_birth,
        gender=member.gender,
        phone=member.phone,
        staff_number=member.staff_number,
        import_source_id=member.import_source_id,
        national_id=member.national_id,
        passport_number=member.passport_number,
        employment=(
            MemberEmployment.model_validate(vars(member.employment)) if member.employment else None
        ),
        last_imported_at=member.last_imported_at,
        suspended_at=member.suspended_at,
        terminated_at=member.terminated_at,
        created_at=member.created_at,
        updated_at=member.updated_at,
        user_id=member.user_id.value if member.user_id else None,
    )


async def _client_names(
    client_repo: ClientRepository, members: Sequence[EligibleMember]
) -> dict[str, str]:
    """Resolve client display names for a page of members, one lookup per client."""
    names: dict[str, str] = {}
    for member in members:
        key = member.client_id.value
        if key in names:
            continue
        client = await client_repo.get_by_id(member.client_id)
        if client:
            names[key] = client.name
    return names


def _next_of_kin_response(contact: MemberNextOfKin) -> MemberNextOfKinResponse:
    return MemberNextOfKinResponse(
        id=contact.id.value,
        tenant_id=contact.tenant_id.value,
        member_id=contact.member_id.value,
        name=contact.name,
        relationship=contact.relationship,
        phone=contact.phone,
        email=contact.email.value if contact.email else None,
        is_primary=contact.is_primary,
        created_at=contact.created_at,
        updated_at=contact.updated_at,
    )


async def _get_member(
    member_id: str, tenant_id: str, member_repo: EligibleMemberRepository
) -> EligibleMember:
    member = await member_repo.get_by_id(EligibleMemberId(member_id))
    if member is None or member.tenant_id.value != tenant_id:
        raise HTTPException(status_code=404, detail="Member not found")
    return member


async def _get_contact(
    member_id: str,
    contact_id: str,
    tenant_id: str,
    member_repo: EligibleMemberRepository,
    next_of_kin_repo: MemberNextOfKinRepository,
) -> MemberNextOfKin:
    member = await _get_member(member_id, tenant_id, member_repo)
    contact = await next_of_kin_repo.get_by_id(MemberNextOfKinId(contact_id))
    if contact is None or contact.tenant_id != member.tenant_id or contact.member_id != member.id:
        raise HTTPException(status_code=404, detail="Next-of-kin contact not found")
    return contact


async def _assert_known_relationship(
    repo: NextOfKinRelationshipRepository, relationship: str
) -> None:
    """Reject a relationship code the taxonomy does not recognise.

    ``member_next_of_kin.relationship`` is a foreign key, so an unknown code
    would fail at the database with an opaque integrity error; check it here
    for a clean 404 instead.
    """
    if await repo.get_by_code(relationship) is None:
        raise HTTPException(
            status_code=404, detail=f"Next-of-kin relationship {relationship!r} not found"
        )


async def _validate_roster_update(
    member: EligibleMember,
    updated: MemberCreate,
    member_repo: EligibleMemberRepository,
) -> None:
    if updated.primary_employee_member_id == member.id.value:
        raise HTTPException(status_code=422, detail="A member cannot be their own primary employee")
    if member.relation == MemberRelation.EMPLOYEE and updated.relation != member.relation:
        beneficiaries = await member_repo.list_for_primary(
            member.tenant_id, member.client_id, member.id, limit=1
        )
        if beneficiaries:
            raise HTTPException(
                status_code=409,
                detail="Reassign this employee's beneficiaries before changing their relationship",
            )
    duplicate = await member_repo.find_by_employer_member_id(
        member.tenant_id, member.client_id, updated.employer_member_id or member.employer_member_id
    )
    if duplicate is not None and duplicate.id != member.id:
        raise HTTPException(status_code=409, detail="Member code already exists for this client")
    await _validate_primary(
        member_repo,
        updated.primary_employee_member_id,
        tenant_id=member.tenant_id.value,
        client_id=member.client_id.value,
    )


async def _client_in_tenant(
    client_id: str,
    tenant_id: str,
    client_repo: ClientRepository,
) -> ClientEntity:
    client = await client_repo.get_by_id(ClientId(client_id))
    if not client or client.tenant_id.value != tenant_id:
        raise HTTPException(status_code=404, detail="Client not found")
    return client


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


async def _audit(
    entity,
    *,
    outbox: OutboxRepository,
    current_user: TokenData,
    request: Request,
    old_entity=None,
) -> None:
    """Audit a roster write through the same path as every other aggregate.

    These routes used to enqueue their own outbox rows, which meant no field
    diff, no client address and no user agent on a roster change.
    """
    await audit_change(
        entity,
        AuditEventHandler(outbox),
        current_user,
        request,
        old_entity=old_entity,
    )


@router.post(
    "",
    response_model=MemberResponse,
    status_code=status.HTTP_201_CREATED,
    responses={
        404: _error_response("Client not found in this tenant"),
        409: _error_response("Member code already exists for this client"),
        422: _error_response("Member code was set on create, or the primary employee is invalid"),
    },
)
@transactional()
async def create_member(
    request: Request,
    data: MemberCreate,
    current_user: TokenData = Depends(require_not_viewer),
    member_repo: EligibleMemberRepository = Depends(get_eligible_member_repository),
    client_repo: ClientRepository = Depends(get_client_repository),
    subject_repo: ClinicalSubjectRepository = Depends(get_clinical_subject_repository),
    link_repo: EligibleMemberClinicalLinkRepository = Depends(
        get_eligible_member_clinical_link_repository
    ),
    outbox: OutboxRepository = Depends(get_outbox_repository),
    db: AsyncSession = Depends(get_db),
):
    client = await _client_in_tenant(data.client_id, current_user.tenant_id, client_repo)
    if data.employer_member_id:
        raise HTTPException(
            status_code=422,
            detail="Member code is issued by the server and cannot be set on create",
        )
    try:
        employer_member_id = await issue_member_code(
            member_repo,
            tenant_id=TenantId(current_user.tenant_id),
            client_id=ClientId(data.client_id),
            client_code=client.code,
        )
    except ValueError as error:
        raise HTTPException(status_code=409, detail=str(error)) from error
    await _validate_primary(
        member_repo,
        data.primary_employee_member_id,
        tenant_id=current_user.tenant_id,
        client_id=data.client_id,
    )
    # A duplicate code is a conflict, matching the 409 the update path returns.
    # Without this the use case's DomainError surfaces as a 400.
    duplicate = await member_repo.find_by_employer_member_id(
        TenantId(current_user.tenant_id), ClientId(data.client_id), employer_member_id
    )
    if duplicate is not None:
        raise HTTPException(status_code=409, detail="Member code already exists for this client")
    use_case = EnrolEligibleMemberUseCase(member_repo, subject_repo, link_repo)
    try:
        member, _ = await _enrol(use_case, data, current_user, employer_member_id)
    except IntegrityError as error:
        # Two concurrent enrolments can pass the check above and still collide
        # on uq_eligible_member_employer_id_per_client. Report the conflict
        # rather than letting it surface as a 500.
        raise HTTPException(
            status_code=409, detail="Member code already exists for this client"
        ) from error
    await _audit(
        member,
        outbox=outbox,
        current_user=current_user,
        request=request,
    )
    return _response(member)


async def _enrol(
    use_case: EnrolEligibleMemberUseCase,
    data: MemberCreate,
    current_user: TokenData,
    employer_member_id: str,
):
    return await use_case.execute(
        tenant_id=TenantId(current_user.tenant_id),
        client_id=ClientId(data.client_id),
        employer_member_id=employer_member_id,
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
        staff_number=data.staff_number,
        import_source_id=data.import_source_id,
        national_id=data.national_id,
        passport_number=data.passport_number,
        employment=_employment(data.employment),
        coverage_start=data.coverage_start,
    )


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
    sort_by: Literal[
        "created_at", "updated_at", "employer_member_id", "display_label", "status", "relation"
    ] = Query("created_at"),
    sort_desc: bool = Query(True),
    member_repo: EligibleMemberRepository = Depends(get_eligible_member_repository),
    client_repo: ClientRepository = Depends(get_client_repository),
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
    names = await _client_names(client_repo, items)
    return MemberListResponse(
        items=[_response(item, names.get(item.client_id.value)) for item in items],
        total=total,
        page=pg.page,
        limit=pg.limit,
        has_more=pg.offset + pg.limit < total,
    )


@router.get("/stats", response_model=MemberStatsResponse)
@readonly()
async def member_stats(
    current_user: TokenData = Depends(get_current_user),
    client_id: str | None = Query(None),
    member_status: EligibilityStatus | None = Query(None, alias="status"),
    relation: MemberRelation | None = Query(None),
    search: str | None = Query(None),
    member_repo: EligibleMemberRepository = Depends(get_eligible_member_repository),
):
    """Aggregate counts for the roster summary strip, honouring the list filters."""
    stats = await member_repo.count_by_status(
        TenantId(current_user.tenant_id),
        client_id=ClientId(client_id) if client_id else None,
        status=member_status,
        relation=relation,
        search=search,
    )
    return MemberStatsResponse(
        total=sum(stats.by_status.values()),
        active=stats.by_status.get(EligibilityStatus.ACTIVE, 0),
        suspended=stats.by_status.get(EligibilityStatus.SUSPENDED, 0),
        pending=stats.by_status.get(EligibilityStatus.PENDING, 0),
        terminated=stats.by_status.get(EligibilityStatus.TERMINATED, 0),
        with_account=stats.with_account,
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
    members: list[EligibleMember] = []
    if member_ids:
        for raw_id in dict.fromkeys(member_ids):
            member = await member_repo.get_by_id(EligibleMemberId(raw_id))
            if member and member.tenant_id == tenant:
                members.append(member)
    else:
        while True:
            batch = await member_repo.list_all(
                tenant,
                client_id=ClientId(client_id) if client_id else None,
                status=member_status,
                relation=relation,
                search=search,
                limit=1000,
                offset=len(members),
                sort_by="created_at",
                sort_desc=True,
            )
            members.extend(batch)
            if len(batch) < 1000:
                break
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
        "staff_number",
        "national_id",
        "passport_number",
    ]
    writer = csv.DictWriter(output, fieldnames=fields)
    writer.writeheader()
    for member in members:
        item = _response(member)
        values = item.model_dump(mode="json")
        writer.writerow({field: _csv_cell(values[field]) for field in fields})
    return StreamingResponse(
        iter([output.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": 'attachment; filename="members.csv"'},
    )


@router.get(
    "/import/template",
    summary="Download the member CSV import template",
)
async def member_import_template(
    current_user: TokenData = Depends(get_current_user),
) -> StreamingResponse:
    """Return the supported member roster columns with one safe example row."""
    output = io.StringIO(newline="")
    writer = csv.writer(output)
    writer.writerow(
        [
            "Company Code",
            "Staff_ID",
            "Staff Number",
            "Name of Employee",
            "Email Address",
            "Personal Email",
            "Date of Birth",
            "Date Joined",
            "Gender",
            "Phone",
            "National ID",
            "Passport Number",
            "Job Title",
            "Job Classification",
            "Skill",
            "Department",
            "Unit",
            "Contract type",
            "Status",
            "Relation",
            "Primary Staff ID",
        ]
    )
    writer.writerow(
        [
            "EXM",
            "EXM-001",
            "001",
            "Example Member",
            "example@company.test",
            "",
            "1990-01-31",
            "",
            "Female",
            "+256700000000",
            "",
            "",
            "",
            "",
            "",
            "",
            "",
            "Pending",
            "Employee",
            "",
        ]
    )
    return StreamingResponse(
        iter([output.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": 'attachment; filename="members-import-template.csv"'},
    )


@router.get(
    "/duplicates",
    response_model=MemberDuplicateListResponse,
    summary="Find members sharing an employer member ID",
)
@readonly()
async def scan_member_duplicates(
    current_user: TokenData = Depends(get_current_user),
    member_repo: EligibleMemberRepository = Depends(get_eligible_member_repository),
    client_repo: ClientRepository = Depends(get_client_repository),
) -> MemberDuplicateListResponse:
    """Find exact tenant/client/member-ID collisions without name or email matching."""
    members: list[EligibleMember] = []
    while True:
        batch = await member_repo.list_all(
            TenantId(current_user.tenant_id),
            limit=1000,
            offset=len(members),
            sort_by="created_at",
            sort_desc=False,
        )
        members.extend(batch)
        if len(batch) < 1000:
            break

    groups: dict[tuple[str, str, str], list[EligibleMember]] = {}
    for member in members:
        key = (member.client_id.value, member.employer_member_id.casefold(), member.tenant_id.value)
        groups.setdefault(key, []).append(member)

    client_names = await _client_names(client_repo, members)
    candidates: list[MemberDuplicateCandidate] = []
    for group in groups.values():
        for first, second in zip(group, group[1:], strict=False):
            candidates.append(
                MemberDuplicateCandidate(
                    first=MemberDuplicateMember(
                        id=first.id.value,
                        client_id=first.client_id.value,
                        client_name=client_names.get(first.client_id.value),
                        employer_member_id=first.employer_member_id,
                        display_label=first.display_label,
                        relation=first.relation,
                    ),
                    second=MemberDuplicateMember(
                        id=second.id.value,
                        client_id=second.client_id.value,
                        client_name=client_names.get(second.client_id.value),
                        employer_member_id=second.employer_member_id,
                        display_label=second.display_label,
                        relation=second.relation,
                    ),
                    reason="Same Staff_ID within the same client",
                )
            )
    return MemberDuplicateListResponse(items=candidates[:100], scanned=len(members))


ROSTER_MAX_BYTES = 10 * 1024 * 1024


async def _read_roster(
    file: UploadFile,
) -> tuple[bytes, list[MemberCsvRow], list[dict[str, object]]]:
    """Decode an uploaded roster into its raw bytes, parsed rows, and parser issues."""
    if not file.filename or not file.filename.lower().endswith(".csv"):
        raise HTTPException(status_code=415, detail="Only CSV files are supported")
    content = await file.read()
    if len(content) > ROSTER_MAX_BYTES:
        raise HTTPException(status_code=413, detail="Member roster CSV must be 10 MB or smaller")
    try:
        rows, issues = parse_member_csv(content)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    return content, rows, issues


@dataclass(frozen=True)
class _RowWriters:
    """The two ways an applied row reaches a member: create one, or revise one."""

    importer: MemberRowImporter
    updater: MemberRowUpdater


def _writers(
    current_user: TokenData,
    member_repo: EligibleMemberRepository,
    subject_repo: ClinicalSubjectRepository,
    link_repo: EligibleMemberClinicalLinkRepository,
    outbox: OutboxRepository,
) -> _RowWriters:
    return _RowWriters(
        importer=MemberRowImporter(
            current_user,
            EnrolEligibleMemberUseCase(member_repo, subject_repo, link_repo),
            member_repo,
            outbox,
            _tenant_secret(current_user.tenant_id),
        ),
        updater=MemberRowUpdater(current_user, member_repo, outbox),
    )


def _batch_response(
    batch: MemberImportBatchEntity, counts: dict[str, int]
) -> MemberImportBatchResponse:
    return MemberImportBatchResponse(
        id=batch.id.value,
        tenant_id=batch.tenant_id.value,
        file_name=batch.file_name,
        file_hash=batch.file_hash,
        row_count=batch.row_count,
        status=batch.status.value,
        outcome_counts=counts,
        staged_by=batch.staged_by.value,
        applied_by=batch.applied_by.value if batch.applied_by else None,
        applied_at=batch.applied_at,
        created_at=batch.created_at,
    )


def _staged_employment(row: MemberImportRowEntity) -> MemberEmployment | None:
    """The row's employment values, or None when the roster carried none."""
    details = EmploymentDetails.build(
        job_title=row.job_title,
        job_classification=row.job_classification,
        skill=row.skill,
        department=row.department,
        unit=row.unit,
        employment_type=row.employment_type,
    )
    return MemberEmployment.model_validate(vars(details)) if details else None


def _row_response(
    row: MemberImportRowEntity, client_name: str | None = None
) -> MemberImportRowResponse:
    return MemberImportRowResponse(
        id=row.id.value,
        row_number=row.row_number,
        client_code=row.client_code,
        client_name=client_name,
        import_source_id=row.import_source_id,
        staff_number=row.staff_number,
        display_label=row.display_label,
        outcome=row.outcome.value,
        decision=row.decision,
        employment=_staged_employment(row),
        message=row.message,
        matched_member_id=row.matched_member_id.value if row.matched_member_id else None,
        imported_member_id=row.imported_member_id.value if row.imported_member_id else None,
    )


async def _require_import_batch(
    imports: MemberImportRepository, tenant_id: str, batch_id: str
) -> MemberImportBatchEntity:
    batch = await imports.get_batch(TenantId(tenant_id), MemberImportBatchId(batch_id))
    if batch is None:
        raise NotFoundError(
            "Import batch not found", resource_type="MemberImportBatch", resource_id=batch_id
        )
    return batch


@router.post(
    "/import",
    response_model=MemberImportBatchResponse,
    status_code=status.HTTP_201_CREATED,
)
@transactional()
async def stage_member_import(
    request: Request,
    file: UploadFile = File(..., description="UTF-8 client member roster CSV"),
    current_user: TokenData = Depends(require_not_viewer),
    imports: MemberImportRepository = Depends(get_member_import_repository),
    member_repo: EligibleMemberRepository = Depends(get_eligible_member_repository),
    client_repo: ClientRepository = Depends(get_client_repository),
    outbox: OutboxRepository = Depends(get_outbox_repository),
    db: AsyncSession = Depends(get_db),
):
    """Stage a roster for review. Writes no members; apply does that.

    Restaging a roster whose batch is still awaiting a decision is a
    conflict, not a second batch. Restaging one already applied or abandoned
    is how a corrected file re-judges against the roster as it now stands.
    """
    content, rows, parse_issues = await _read_roster(file)
    parse_errors = {int(issue["row"]): str(issue["message"]) for issue in parse_issues}
    tenant = TenantId(current_user.tenant_id)
    file_hash = "sha256:" + hashlib.sha256(content).hexdigest()

    existing = await imports.find_batch_by_hash(tenant, file_hash)
    if existing is not None and existing.status is ImportBatchStatus.STAGED:
        message = f"This file was already staged as batch {existing.id.value}"
        raise DomainError(
            message,
            error_code="IMPORT_ALREADY_STAGED",
            http_status=409,
            details={"file": message, "batch_id": existing.id.value},
        )
    await imports.release_superseded_rows(tenant, file_hash)

    now = utc_now()
    batch = MemberImportBatchEntity(
        id=MemberImportBatchId(generate_cuid()),
        tenant_id=tenant,
        file_name=file.filename or "upload",
        file_hash=file_hash,
        row_count=len(rows),
        staged_by=UserId(current_user.user_id),
        created_at=now,
        updated_at=now,
    )
    batch.mark_staged(at=now)
    await imports.save_batch(batch)

    checker = MemberRowChecker(current_user.tenant_id, client_repo, member_repo, imports)
    with measure_queries() as measured:
        await checker.preload(rows, file_hash)
        entities: list[MemberImportRowEntity] = []
        for row in rows:
            check = await checker.check(
                row, parse_error=parse_errors.get(row.row_number), file_hash=file_hash
            )
            entities.append(
                build_row_entity(
                    row,
                    check,
                    row_id=MemberImportRowId(generate_cuid()),
                    batch_id=batch.id,
                    tenant_id=tenant,
                    file_hash=file_hash,
                    now=now,
                )
            )
        await imports.add_rows(entities)
    logger.info(
        "member import staged",
        extra={
            "import_kind": "members",
            "import_phase": "stage",
            "batch_id": batch.id.value,
            "rows": len(rows),
            **measured.as_log_fields(len(rows)),
        },
    )
    await _audit(batch, outbox=outbox, current_user=current_user, request=request)
    return _batch_response(batch, await imports.outcome_counts(tenant, batch.id))


@router.get("/import/{batch_id}", response_model=MemberImportBatchResponse)
@readonly()
async def get_member_import_batch(
    batch_id: str,
    current_user: TokenData = Depends(get_current_user),
    imports: MemberImportRepository = Depends(get_member_import_repository),
):
    batch = await _require_import_batch(imports, current_user.tenant_id, batch_id)
    return _batch_response(
        batch, await imports.outcome_counts(TenantId(current_user.tenant_id), batch.id)
    )


@router.get("/import/{batch_id}/rows", response_model=MemberImportRowListResponse)
@readonly()
async def list_member_import_rows(
    batch_id: str,
    outcome: str | None = Query(None, description="Filter the review queue"),
    pg: PageParams = Depends(pagination(default_limit=50, max_limit=200)),
    current_user: TokenData = Depends(get_current_user),
    imports: MemberImportRepository = Depends(get_member_import_repository),
    client_repo: ClientRepository = Depends(get_client_repository),
):
    tenant = TenantId(current_user.tenant_id)
    items, total = await imports.list_rows(
        tenant, MemberImportBatchId(batch_id), outcome=outcome, limit=pg.limit, offset=pg.offset
    )
    names: dict[str, str] = {}
    for row in items:
        if row.client_id and row.client_id.value not in names:
            client = await client_repo.get_by_id(row.client_id)
            if client:
                names[row.client_id.value] = client.name
    return MemberImportRowListResponse(
        items=[
            _row_response(row, names.get(row.client_id.value) if row.client_id else None)
            for row in items
        ],
        total=total,
        page=pg.page,
        limit=pg.limit,
        has_more=(pg.offset + len(items)) < total,
    )


@router.patch("/import/{batch_id}/rows/{row_id}", response_model=MemberImportRowResponse)
@transactional()
async def set_member_import_row_decision(
    batch_id: str,
    row_id: str,
    data: MemberImportRowDecisionRequest,
    current_user: TokenData = Depends(require_not_viewer),
    imports: MemberImportRepository = Depends(get_member_import_repository),
    db: AsyncSession = Depends(get_db),
):
    """Set one reviewed row's decision before the batch is applied.

    A New row takes import or skip; a duplicate that matched a member takes
    update or skip. Any other row refuses every decision.
    """
    tenant = TenantId(current_user.tenant_id)
    row = await imports.get_row(tenant, MemberImportBatchId(batch_id), MemberImportRowId(row_id))
    if row is None:
        raise NotFoundError(
            "Import row not found", resource_type="MemberImportRow", resource_id=row_id
        )
    row.set_decision(data.decision)
    await imports.set_row_decision(tenant, row.id, row.decision)
    return _row_response(row)


@router.post("/import/{batch_id}/abandon", response_model=MemberImportBatchResponse)
@transactional()
async def abandon_member_import(
    batch_id: str,
    data: MemberImportAbandonRequest,
    request: Request,
    current_user: TokenData = Depends(require_not_viewer),
    imports: MemberImportRepository = Depends(get_member_import_repository),
    outbox: OutboxRepository = Depends(get_outbox_repository),
    db: AsyncSession = Depends(get_db),
):
    """Close a batch nobody will apply, with the reason on the record.

    Frees the file hash and this batch's rows' Staff_IDs, so the roster can
    be staged again once whatever blocked it is fixed.
    """
    tenant = TenantId(current_user.tenant_id)
    batch = await _require_import_batch(imports, current_user.tenant_id, batch_id)
    batch.abandon(UserId(current_user.user_id), data.reason, at=utc_now())
    await imports.save_batch(batch)
    await imports.release_replay_keys(tenant, batch.id)
    await _audit(batch, outbox=outbox, current_user=current_user, request=request)
    return _batch_response(batch, await imports.outcome_counts(tenant, batch.id))


class _ClaimLost(Exception):
    """Another apply of this batch claimed the row first."""


async def _write_row(
    row: MemberImportRowEntity,
    checker: MemberRowChecker,
    writers: _RowWriters,
    imports: MemberImportRepository,
    tenant_id: TenantId,
    db: AsyncSession,
) -> str:
    """Re-check and write one pending row inside its own savepoint.

    A batch can sit staged for a while before it is applied, so the row is
    judged again against the roster as it stands now rather than trusted from
    staging time. Leaving the savepoint by raising undoes this row's writes
    and leaves the rows around it in the same call standing, so a row that
    fails is marked Failed and the caller's loop continues: see "Roster import
    atomicity" in docs/migrations/MEMBERS_MIGRATION.md.
    """
    csv_row = csv_row_from_entity(row)
    check = await checker.check(csv_row)
    try:
        async with db.begin_nested():
            return await _write_checked_row(row, csv_row, check, writers, imports, tenant_id)
    except _ClaimLost:
        return "unchanged"
    except (EvexiaException, IntegrityError, ValueError) as exc:
        await imports.mark_row_failed(tenant_id, row.id, str(exc).split("\n", 1)[-1])
        return "failed"


async def _write_checked_row(
    row: MemberImportRowEntity,
    csv_row: MemberCsvRow,
    check: RowCheck,
    writers: _RowWriters,
    imports: MemberImportRepository,
    tenant_id: TenantId,
) -> str:
    """Enrol or revise the member this row resolved to, and claim the row for it."""
    if row.decision == "update":
        return await _revise_member(row, csv_row, check, writers, imports, tenant_id)
    if not check.importable or check.data is None or check.client is None:
        await imports.mark_row_failed(
            tenant_id, row.id, check.message or f"No longer importable ({check.state})"
        )
        return "failed"
    member = await writers.importer.enrol(csv_row, check.data, check.client.code)
    if not await imports.mark_row_imported(tenant_id, row.id, member.id.value):
        raise _ClaimLost
    return "imported"


async def _revise_member(
    row: MemberImportRowEntity,
    csv_row: MemberCsvRow,
    check: RowCheck,
    writers: _RowWriters,
    imports: MemberImportRepository,
    tenant_id: TenantId,
) -> str:
    if not check.updatable or check.existing is None:
        await imports.mark_row_failed(
            tenant_id, row.id, check.message or f"No longer updatable ({check.state})"
        )
        return "failed"
    changed = await writers.updater.update(csv_row, check.existing)
    claimed = await imports.mark_row_imported(
        tenant_id,
        row.id,
        check.existing.id.value,
        message=None if changed else "No changes: roster matches the member already",
    )
    if not claimed:
        raise _ClaimLost
    return "updated" if changed else "unchanged"


async def _apply_rows(
    tenant_id: TenantId,
    batch_id: MemberImportBatchId,
    checker: MemberRowChecker,
    writers: _RowWriters,
    imports: MemberImportRepository,
    db: AsyncSession,
    committer: BatchedCommit,
    *,
    limit: int,
) -> dict[str, int]:
    """Write up to `limit` still-pending rows, one at a time.

    Fetches only rows `apply_member_import` has not yet resolved (a New row
    decided "import", a matched Duplicate decided "update", neither yet
    written) instead of paging through the whole batch, so a later chunk of a
    large batch costs one query for exactly what is left, not a re-scan of
    everything already written.
    """
    tally = {"imported": 0, "updated": 0, "unchanged": 0, "failed": 0}
    rows = await imports.list_pending_rows(tenant_id, batch_id, limit=limit)
    for row in rows:
        state = await _write_row(row, checker, writers, imports, tenant_id, db)
        tally[state] += 1
        await committer.after_row()
    await committer.flush()
    return tally


@router.post("/import/{batch_id}/apply", response_model=MemberImportApplyResponse)
@readonly()
async def apply_member_import(
    batch_id: str,
    request: Request,
    limit: int = Query(
        100,
        ge=1,
        le=500,
        description="Max rows to write in this call. Keep calling while the response's "
        "remaining is above zero; the batch only closes once nothing is left.",
    ),
    current_user: TokenData = Depends(require_not_viewer),
    imports: MemberImportRepository = Depends(get_member_import_repository),
    member_repo: EligibleMemberRepository = Depends(get_eligible_member_repository),
    client_repo: ClientRepository = Depends(get_client_repository),
    subject_repo: ClinicalSubjectRepository = Depends(get_clinical_subject_repository),
    link_repo: EligibleMemberClinicalLinkRepository = Depends(
        get_eligible_member_clinical_link_repository
    ),
    outbox: OutboxRepository = Depends(get_outbox_repository),
    db: AsyncSession = Depends(get_db),
):
    """Write up to `limit` still-pending rows, one at a time, in their own transaction.

    A roster of thousands of rows cannot be written in a single call without
    risking a platform request timeout, since each row costs its own
    round trip and commit. Call this repeatedly while `remaining` in the
    response is above zero; `list_pending_rows` re-queries what is left each
    time rather than trusting an offset, so a client that stops calling
    (a closed tab, a timeout) leaves the batch safely Staged for the next
    call to continue from exactly where the last one left off, with nothing
    skipped or written twice. The batch only closes -- flips to Applied,
    fires its audit event -- once a call finds nothing left to write.
    """
    batch = await _require_import_batch(imports, current_user.tenant_id, batch_id)
    if batch.status is not ImportBatchStatus.STAGED:
        raise DomainError(
            f"Batch {batch_id} is {batch.status.value} and cannot be applied again",
            error_code="import_batch_not_staged",
            http_status=409,
        )
    tenant = TenantId(current_user.tenant_id)
    checker = MemberRowChecker(current_user.tenant_id, client_repo, member_repo, imports)
    writers = _writers(current_user, member_repo, subject_repo, link_repo, outbox)
    committer = BatchedCommit(db.commit)
    with measure_queries() as measured:
        tally = await _apply_rows(
            tenant, batch.id, checker, writers, imports, db, committer, limit=limit
        )
    written = sum(tally.values())
    logger.info(
        "member import chunk applied",
        extra={
            "import_kind": "members",
            "import_phase": "apply",
            "batch_id": batch_id,
            "rows": written,
            "commits": committer.commits,
            **tally,
            **measured.as_log_fields(written),
        },
    )
    remaining = await imports.count_pending_rows(tenant, batch.id)
    if remaining == 0:
        accepted_count = await imports.count_imported_rows(tenant, batch.id)
        batch.mark_applied(
            UserId(current_user.user_id), at=utc_now(), accepted_count=accepted_count
        )
        await imports.save_batch(batch)
        await _audit(batch, outbox=outbox, current_user=current_user, request=request)
    await db.commit()
    return MemberImportApplyResponse(
        batch_id=batch_id,
        imported=tally["imported"],
        updated=tally["updated"],
        unchanged=tally["unchanged"],
        failed=tally["failed"],
        remaining=remaining,
        done=remaining == 0,
    )


def _csv_cell(value: str | None) -> str | None:
    # Spreadsheet applications interpret these prefixes even in quoted CSV cells.
    if isinstance(value, str) and value.lstrip().startswith(("=", "+", "-", "@", "\t", "\r", "\n")):
        return "'" + value
    return value


@router.patch(
    "/{member_id}",
    response_model=MemberResponse,
    responses={
        404: _error_response("Member not found"),
        409: _error_response("Member code already exists, or beneficiaries block the change"),
        422: _error_response("Update would leave the member invalid, or names itself as primary"),
    },
)
@transactional()
async def update_member(
    request: Request,
    member_id: str,
    data: MemberUpdate,
    current_user: TokenData = Depends(require_not_viewer),
    member_repo: EligibleMemberRepository = Depends(get_eligible_member_repository),
    outbox: OutboxRepository = Depends(get_outbox_repository),
    db: AsyncSession = Depends(get_db),
):
    member = await _get_member(member_id, current_user.tenant_id, member_repo)
    values = _response(member).model_dump(include=set(MemberCreate.model_fields))
    values.update(data.model_dump(exclude_unset=True))
    try:
        updated = MemberCreate.model_validate(values)
    except ValidationError as error:
        raise HTTPException(
            status_code=422,
            detail="Member update must retain a valid name, member code and beneficiary relationship",
        ) from error
    await _validate_roster_update(member, updated, member_repo)
    # update_roster_details mutates in place, so the diff needs the state first.
    before = deepcopy(member)
    # import_source_id and coverage_start are set once (at creation, or import)
    # and never revised through this general roster-details update; each stays
    # whatever the member was created with.
    details = updated.model_dump(exclude={"client_id", "import_source_id", "coverage_start"})
    details["primary_employee_member_id"] = (
        EligibleMemberId(updated.primary_employee_member_id)
        if updated.primary_employee_member_id
        else None
    )
    details["employer_member_id"] = updated.employer_member_id or member.employer_member_id
    details["work_email"] = Email(str(updated.work_email)) if updated.work_email else None
    details["personal_email"] = (
        Email(str(updated.personal_email)) if updated.personal_email else None
    )
    details["employment"] = _employment(updated.employment)
    member.update_roster_details(
        **details, coverage_start=member.coverage_start, coverage_end=member.coverage_end
    )
    await member_repo.save(member)
    await _audit(
        member,
        outbox=outbox,
        current_user=current_user,
        request=request,
        old_entity=before,
    )
    return _response(member)


async def _transition_member(
    member_id: str,
    action: str,
    current_user: TokenData,
    member_repo: EligibleMemberRepository,
):
    member = await _get_member(member_id, current_user.tenant_id, member_repo)
    getattr(member, action)()
    await member_repo.save(member)
    return member


@router.put(
    "/{member_id}/account",
    response_model=MemberResponse,
    responses={
        404: _error_response("Member or user account not found"),
        409: _error_response("User account is linked to another member"),
    },
)
@transactional()
async def link_member_account(
    request: Request,
    member_id: str,
    data: MemberAccountLinkRequest,
    current_user: TokenData = Depends(get_current_user),
    _admin=Depends(require_tenant_role(TenantRole.ADMIN)),
    member_repo: EligibleMemberRepository = Depends(get_eligible_member_repository),
    user_repo: UserRepository = Depends(get_user_repository),
    outbox: OutboxRepository = Depends(get_outbox_repository),
    db: AsyncSession = Depends(get_db),
):
    member = await _get_member(member_id, current_user.tenant_id, member_repo)
    user = await user_repo.get_by_id(UserId(data.user_id))
    if user is None or user.tenant_id != member.tenant_id or user.deleted_at is not None:
        raise HTTPException(status_code=404, detail="User account not found")
    linked = await member_repo.find_by_user_id(member.tenant_id, user.id)
    if linked is not None and linked.id != member.id:
        raise HTTPException(status_code=409, detail="User account is linked to another member")
    member.link_account(user.id)
    await member_repo.save(member)
    # Linkage is an association between two aggregates, so the route names it
    # rather than the member's own methods.
    member.events.append(
        EligibleMemberAccountLinked(
            occurred_at=utc_now(), member_id=member.id, user_id=str(member.user_id)
        )
    )
    await _audit(
        member,
        outbox=outbox,
        current_user=current_user,
        request=request,
    )
    return _response(member)


@router.delete("/{member_id}/account", response_model=MemberResponse)
@transactional()
async def unlink_member_account(
    request: Request,
    member_id: str,
    current_user: TokenData = Depends(get_current_user),
    _admin=Depends(require_tenant_role(TenantRole.ADMIN)),
    member_repo: EligibleMemberRepository = Depends(get_eligible_member_repository),
    outbox: OutboxRepository = Depends(get_outbox_repository),
    db: AsyncSession = Depends(get_db),
):
    member = await _get_member(member_id, current_user.tenant_id, member_repo)
    member.unlink_account()
    await member_repo.save(member)
    # Linkage is an association between two aggregates, so the route names it
    # rather than the member's own methods.
    member.events.append(EligibleMemberAccountUnlinked(occurred_at=utc_now(), member_id=member.id))
    await _audit(
        member,
        outbox=outbox,
        current_user=current_user,
        request=request,
    )
    return _response(member)


@router.post(
    "/{member_id}/merge",
    response_model=MemberMergeResponse,
    responses={
        404: _error_response("Target or source member not found"),
        409: _error_response("Members belong to different clients"),
        422: _error_response("Source and target members must differ"),
    },
)
@transactional()
async def merge_members(
    request: Request,
    member_id: str,
    data: MemberMergeRequest,
    current_user: TokenData = Depends(get_current_user),
    _admin=Depends(require_tenant_role(TenantRole.ADMIN)),
    member_repo: EligibleMemberRepository = Depends(get_eligible_member_repository),
    outbox: OutboxRepository = Depends(get_outbox_repository),
    db: AsyncSession = Depends(get_db),
):
    if data.source_member_id == member_id:
        raise HTTPException(status_code=422, detail="Source and target members must differ")
    target = await _get_member(member_id, current_user.tenant_id, member_repo)
    source = await _get_member(data.source_member_id, current_user.tenant_id, member_repo)
    if target.client_id != source.client_id:
        raise HTTPException(status_code=409, detail="Members must belong to the same client")
    transferred = await member_repo.merge_into(target.tenant_id, source.id, target.id)
    target.events.append(
        EligibleMemberMerged(
            occurred_at=utc_now(), member_id=target.id, merged_from=source.id.value
        )
    )
    source.events.append(
        EligibleMemberMergedIntoMember(
            occurred_at=utc_now(), member_id=source.id, merged_into=target.id.value
        )
    )
    await _audit(
        target,
        outbox=outbox,
        current_user=current_user,
        request=request,
    )
    await _audit(
        source,
        outbox=outbox,
        current_user=current_user,
        request=request,
    )
    return MemberMergeResponse(
        member=_response(await _get_member(member_id, current_user.tenant_id, member_repo)),
        source_member_id=source.id.value,
        transferred=transferred,
    )


@router.post("/{member_id}/suspend", response_model=MemberResponse)
@transactional()
async def suspend_member(
    request: Request,
    member_id: str,
    current_user: TokenData = Depends(require_not_viewer),
    member_repo: EligibleMemberRepository = Depends(get_eligible_member_repository),
    outbox: OutboxRepository = Depends(get_outbox_repository),
    db: AsyncSession = Depends(get_db),
):
    member = await _transition_member(member_id, "suspend", current_user, member_repo)
    await _audit(
        member,
        outbox=outbox,
        current_user=current_user,
        request=request,
    )
    return _response(member)


@router.post("/{member_id}/reinstate", response_model=MemberResponse)
@transactional()
async def reinstate_member(
    request: Request,
    member_id: str,
    current_user: TokenData = Depends(require_not_viewer),
    member_repo: EligibleMemberRepository = Depends(get_eligible_member_repository),
    outbox: OutboxRepository = Depends(get_outbox_repository),
    db: AsyncSession = Depends(get_db),
):
    member = await _transition_member(member_id, "reinstate", current_user, member_repo)
    await _audit(
        member,
        outbox=outbox,
        current_user=current_user,
        request=request,
    )
    return _response(member)


@router.post("/{member_id}/terminate", response_model=MemberResponse)
@transactional()
async def terminate_member(
    request: Request,
    member_id: str,
    current_user: TokenData = Depends(require_not_viewer),
    member_repo: EligibleMemberRepository = Depends(get_eligible_member_repository),
    outbox: OutboxRepository = Depends(get_outbox_repository),
    db: AsyncSession = Depends(get_db),
):
    member = await _transition_member(member_id, "terminate", current_user, member_repo)
    await _audit(
        member,
        outbox=outbox,
        current_user=current_user,
        request=request,
    )
    return _response(member)


@router.get("/{member_id}/beneficiaries", response_model=list[MemberResponse])
@readonly()
async def list_member_beneficiaries(
    member_id: str,
    current_user: TokenData = Depends(get_current_user),
    member_repo: EligibleMemberRepository = Depends(get_eligible_member_repository),
):
    member = await _get_member(member_id, current_user.tenant_id, member_repo)
    if member.relation != MemberRelation.EMPLOYEE:
        return []
    beneficiaries = await member_repo.list_for_primary(
        TenantId(current_user.tenant_id),
        member.client_id,
        member.id,
    )
    return [_response(item) for item in beneficiaries]


@router.get("/{member_id}/sessions", response_model=ServiceSessionListResponse)
@readonly()
async def list_member_sessions(
    member_id: str,
    current_user: TokenData = Depends(require_clinical_scope),
    pg: PageParams = Depends(pagination()),
    member_repo: EligibleMemberRepository = Depends(get_eligible_member_repository),
    session_repo: ServiceSessionRepository = Depends(get_service_session_repository),
    db: AsyncSession = Depends(get_db),
):
    member = await _get_member(member_id, current_user.tenant_id, member_repo)
    items = await session_repo.list_all(
        tenant_id=member.tenant_id,
        member_id=member.id,
        limit=pg.limit,
        offset=pg.offset,
        sort_by="scheduled_at",
        sort_desc=True,
    )
    total = await session_repo.count(tenant_id=member.tenant_id, member_id=member.id)
    return ServiceSessionListResponse(
        items=[to_service_session_response(item) for item in items],
        total=total,
        page=pg.page,
        limit=pg.limit,
        has_more=pg.offset + pg.limit < total,
    )


@router.get("/{member_id}/next-of-kin", response_model=list[MemberNextOfKinResponse])
@readonly()
async def list_member_next_of_kin(
    member_id: str,
    current_user: TokenData = Depends(get_current_user),
    member_repo: EligibleMemberRepository = Depends(get_eligible_member_repository),
    next_of_kin_repo: MemberNextOfKinRepository = Depends(get_member_next_of_kin_repository),
):
    member = await _get_member(member_id, current_user.tenant_id, member_repo)
    contacts = await next_of_kin_repo.list_for_member(TenantId(current_user.tenant_id), member.id)
    return [_next_of_kin_response(contact) for contact in contacts]


@router.post(
    "/{member_id}/next-of-kin",
    response_model=MemberNextOfKinResponse,
    status_code=status.HTTP_201_CREATED,
)
@transactional()
async def create_member_next_of_kin(
    request: Request,
    member_id: str,
    data: MemberNextOfKinCreate,
    current_user: TokenData = Depends(require_not_viewer),
    member_repo: EligibleMemberRepository = Depends(get_eligible_member_repository),
    next_of_kin_repo: MemberNextOfKinRepository = Depends(get_member_next_of_kin_repository),
    relationship_repo: NextOfKinRelationshipRepository = Depends(
        get_next_of_kin_relationship_repository
    ),
    outbox: OutboxRepository = Depends(get_outbox_repository),
    db: AsyncSession = Depends(get_db),
):
    member = await _get_member(member_id, current_user.tenant_id, member_repo)
    await _assert_known_relationship(relationship_repo, data.relationship)
    now = utc_now()
    contact = MemberNextOfKin(
        id=MemberNextOfKinId(generate_cuid()),
        tenant_id=TenantId(current_user.tenant_id),
        member_id=member.id,
        name=data.name.strip(),
        relationship=data.relationship,
        phone=data.phone.strip() if data.phone else None,
        email=Email(str(data.email)) if data.email else None,
        is_primary=data.is_primary,
        created_at=now,
        updated_at=now,
    )
    await next_of_kin_repo.save(contact)
    contact.events.append(
        MemberNextOfKinCreated(occurred_at=utc_now(), member_id=contact.member_id)
    )
    await _audit(
        contact,
        outbox=outbox,
        current_user=current_user,
        request=request,
    )
    return _next_of_kin_response(contact)


@router.patch("/{member_id}/next-of-kin/{contact_id}", response_model=MemberNextOfKinResponse)
@transactional()
async def update_member_next_of_kin(
    request: Request,
    member_id: str,
    contact_id: str,
    data: MemberNextOfKinUpdate,
    current_user: TokenData = Depends(require_not_viewer),
    member_repo: EligibleMemberRepository = Depends(get_eligible_member_repository),
    next_of_kin_repo: MemberNextOfKinRepository = Depends(get_member_next_of_kin_repository),
    relationship_repo: NextOfKinRelationshipRepository = Depends(
        get_next_of_kin_relationship_repository
    ),
    outbox: OutboxRepository = Depends(get_outbox_repository),
    db: AsyncSession = Depends(get_db),
):
    contact = await _get_contact(
        member_id, contact_id, current_user.tenant_id, member_repo, next_of_kin_repo
    )
    await _assert_known_relationship(relationship_repo, data.relationship)
    before = deepcopy(contact)
    contact.update(
        name=data.name.strip(),
        relationship=data.relationship,
        phone=data.phone.strip() if data.phone else None,
        email=Email(str(data.email)) if data.email else None,
        is_primary=data.is_primary,
        now=utc_now(),
    )
    await next_of_kin_repo.save(contact)
    contact.events.append(
        MemberNextOfKinUpdated(occurred_at=utc_now(), member_id=contact.member_id)
    )
    await _audit(
        contact,
        outbox=outbox,
        current_user=current_user,
        request=request,
        old_entity=before,
    )
    return _next_of_kin_response(contact)


@router.delete("/{member_id}/next-of-kin/{contact_id}", status_code=status.HTTP_204_NO_CONTENT)
@transactional()
async def delete_member_next_of_kin(
    request: Request,
    member_id: str,
    contact_id: str,
    current_user: TokenData = Depends(require_not_viewer),
    member_repo: EligibleMemberRepository = Depends(get_eligible_member_repository),
    next_of_kin_repo: MemberNextOfKinRepository = Depends(get_member_next_of_kin_repository),
    outbox: OutboxRepository = Depends(get_outbox_repository),
    db: AsyncSession = Depends(get_db),
):
    contact = await _get_contact(
        member_id, contact_id, current_user.tenant_id, member_repo, next_of_kin_repo
    )
    await next_of_kin_repo.delete(contact.id)
    contact.events.append(
        MemberNextOfKinDeleted(occurred_at=utc_now(), member_id=contact.member_id)
    )
    await _audit(
        contact,
        outbox=outbox,
        current_user=current_user,
        request=request,
    )
    return None


@router.get("/{member_id}", response_model=MemberResponse)
@readonly()
async def get_member(
    member_id: str,
    current_user: TokenData = Depends(get_current_user),
    member_repo: EligibleMemberRepository = Depends(get_eligible_member_repository),
    client_repo: ClientRepository = Depends(get_client_repository),
):
    member = await _get_member(member_id, current_user.tenant_id, member_repo)
    names = await _client_names(client_repo, [member])
    return _response(member, names.get(member.client_id.value))
