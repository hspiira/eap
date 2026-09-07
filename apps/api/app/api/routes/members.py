"""Tenant-facing Members API.

Members are client-covered people, not providers or tenant staff. The existing
``eligible_members`` aggregate is the employer-side source of truth and is
also the only identity-bearing side allowed to link to clinical subjects.
"""

import csv
import io
import json
from collections.abc import Sequence
from typing import Literal

from fastapi import APIRouter, Depends, File, Form, HTTPException, Query, UploadFile, status
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
    get_member_next_of_kin_repository,
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
    MemberImportCommitRequest,
    MemberImportCommitResponse,
    MemberImportResponse,
    MemberImportRowPreview,
    MemberImportRowResult,
    MemberListResponse,
    MemberMergeRequest,
    MemberMergeResponse,
    MemberNextOfKinCreate,
    MemberNextOfKinResponse,
    MemberNextOfKinUpdate,
    MemberResponse,
    MemberUpdate,
)
from app.api.schemas.service_session_schemas import ServiceSessionListResponse
from app.api.services.member_import import (
    MemberRowChecker,
    MemberRowImporter,
    RowCheck,
    csv_row,
    row_values,
)
from app.application.services.member_audit import record_member_change
from app.application.use_cases.eligible_member_use_cases import EnrolEligibleMemberUseCase
from app.core.authorization import require_clinical_scope, require_not_viewer, require_tenant_role
from app.core.database import get_db
from app.core.security import TokenData, get_current_user
from app.domain.entities.client import ClientEntity
from app.domain.entities.eligible_member import EligibleMember
from app.domain.entities.member_next_of_kin import MemberNextOfKin
from app.domain.enums import EligibilityStatus, MemberRelation, TenantRole
from app.domain.exceptions import EvexiaException
from app.domain.repositories.client_repository import ClientRepository
from app.domain.repositories.eligible_member_repository import (
    ClinicalSubjectRepository,
    EligibleMemberClinicalLinkRepository,
    EligibleMemberRepository,
)
from app.domain.repositories.member_next_of_kin_repository import MemberNextOfKinRepository
from app.domain.repositories.outbox_repository import OutboxRepository
from app.domain.repositories.service_session_repository import ServiceSessionRepository
from app.domain.repositories.user_repository import UserRepository
from app.domain.value_objects.core import (
    ClientId,
    EligibleMemberId,
    Email,
    MemberNextOfKinId,
    TenantId,
    UserId,
)
from app.shared.decorators import readonly, transactional
from app.shared.utils.datetime import utc_now
from app.shared.utils.generators import generate_cuid
from app.shared.utils.member_csv import MemberCsvRow, parse_member_csv

router = APIRouter(prefix="/members", tags=["members"])


def _member_import_row(
    row: MemberCsvRow,
    *,
    client_name: str | None = None,
    state: str = "new",
    message: str | None = None,
    default_action: str | None = None,
) -> MemberImportRowPreview:
    return MemberImportRowPreview(
        row=row.row_number,
        client_code=row.client_code,
        client_name=client_name,
        employer_member_id=row.employer_member_id,
        staff_number=row.staff_number,
        display_label=row.display_label,
        state=state,
        message=message,
        default_action=default_action or ("skip" if state == "duplicate" else "import"),
        values=row_values(row),
    )


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
        work_email=member.work_email.value if member.work_email else None,
        personal_email=member.personal_email.value if member.personal_email else None,
        display_label=member.display_label,
        date_of_birth=member.date_of_birth,
        gender=member.gender,
        phone=member.phone,
        staff_number=member.staff_number,
        national_id=member.national_id,
        passport_number=member.passport_number,
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


async def _issue_member_id(
    member_repo: EligibleMemberRepository,
    *,
    tenant_id: TenantId,
    client_id: ClientId,
    client_code: str,
) -> str:
    """Issue the next ``{client code}-###`` id for this client.

    Skips codes already taken, so a roster imported with hand-written codes
    under the same prefix continues from the top rather than colliding.

    This sees only committed rows, so it cannot resolve a race between two
    in-flight enrolments. The unique constraint is what actually guarantees
    uniqueness; ``create_member`` turns that violation into a 409.
    """
    prefix = client_code.strip().upper()
    sequence = await member_repo.next_member_sequence(tenant_id, client_id, prefix)
    for candidate_sequence in range(sequence, sequence + 50):
        candidate = f"{prefix}-{candidate_sequence:03d}"
        existing = await member_repo.find_by_employer_member_id(tenant_id, client_id, candidate)
        if existing is None:
            return candidate
    raise HTTPException(status_code=409, detail="Could not issue a member ID for this client")


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
    employer_member_id = data.employer_member_id or await _issue_member_id(
        member_repo,
        tenant_id=TenantId(current_user.tenant_id),
        client_id=ClientId(data.client_id),
        client_code=client.code,
    )
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
    await record_member_change(
        outbox,
        tenant_id=current_user.tenant_id,
        user_id=current_user.user_id,
        resource_id=member.id.value,
        action="CREATE",
        operation="Created",
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
        national_id=data.national_id,
        passport_number=data.passport_number,
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
async def member_import_template() -> StreamingResponse:
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
            "Gender",
            "Phone",
            "National ID",
            "Passport Number",
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
            "Female",
            "+256700000000",
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


async def _read_roster(file: UploadFile) -> tuple[list[MemberCsvRow], list[dict[str, object]]]:
    """Decode an uploaded roster into parsed rows plus per-row parser issues."""
    if not file.filename or not file.filename.lower().endswith(".csv"):
        raise HTTPException(status_code=415, detail="Only CSV files are supported")
    content = await file.read()
    if len(content) > ROSTER_MAX_BYTES:
        raise HTTPException(status_code=413, detail="Member roster CSV must be 10 MB or smaller")
    try:
        return parse_member_csv(content)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc


def _decisions(raw: str | None) -> dict[str, str]:
    try:
        decoded = json.loads(raw) if raw else {}
    except (TypeError, ValueError, json.JSONDecodeError) as exc:
        raise HTTPException(status_code=422, detail="decisions_json must be an object") from exc
    if not isinstance(decoded, dict):
        raise HTTPException(status_code=422, detail="decisions_json must be an object")
    return decoded


def _decision_for(decisions: dict[str, str], row_number: int) -> str | None:
    return decisions.get(str(row_number), decisions.get(row_number))


def _importer(
    current_user: TokenData,
    member_repo: EligibleMemberRepository,
    subject_repo: ClinicalSubjectRepository,
    link_repo: EligibleMemberClinicalLinkRepository,
    outbox: OutboxRepository,
) -> MemberRowImporter:
    return MemberRowImporter(
        current_user,
        EnrolEligibleMemberUseCase(member_repo, subject_repo, link_repo),
        member_repo,
        outbox,
        _tenant_secret(current_user.tenant_id),
    )


async def _import_row(
    row: MemberCsvRow,
    check: RowCheck,
    importer: MemberRowImporter,
    db: AsyncSession,
) -> MemberImportRowResult:
    """Write one checked row in its own transaction and report what happened."""
    if check.state != "new" or check.data is None:
        return MemberImportRowResult(row=row.row_number, state=check.state, message=check.message)
    try:
        member = await importer.enrol(row, check.data)
        await db.commit()
    except (EvexiaException, IntegrityError, ValueError) as exc:
        await db.rollback()
        return MemberImportRowResult(
            row=row.row_number, state="failed", message=str(exc).split("\n", 1)[-1]
        )
    return MemberImportRowResult(row=row.row_number, state="imported", member_id=member.id.value)


@router.post("/import", response_model=MemberImportResponse)
@readonly()
async def import_members(
    file: UploadFile = File(..., description="UTF-8 client member roster CSV"),
    decisions_json: str | None = Form(None, description="Row decisions from the preview"),
    dry_run: bool = Query(True, description="Preview only; set false to create members"),
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
    """Check a roster row by row, and on confirmation import each row on its own."""
    rows, parse_issues = await _read_roster(file)
    decisions = _decisions(decisions_json)
    parse_errors = {int(issue["row"]): str(issue["message"]) for issue in parse_issues}
    error_fields = {
        int(issue["row"]): str(issue.get("field")) if issue.get("field") else None
        for issue in parse_issues
    }

    checker = MemberRowChecker(current_user.tenant_id, client_repo, member_repo)
    checked: list[tuple[MemberCsvRow, RowCheck]] = []
    for row in rows:
        check = await checker.check(
            row,
            decision=_decision_for(decisions, row.row_number),
            parse_error=parse_errors.get(row.row_number),
        )
        checked.append((row, check))

    previews = [
        _member_import_row(
            row,
            client_name=check.client.name if check.client else None,
            state=check.state,
            message=check.message,
        )
        for row, check in checked
    ]
    skipped = sum(preview.state in {"duplicate", "skipped"} for preview in previews)
    invalid = [preview for preview in previews if preview.state == "invalid"]
    ready = [(row, check) for row, check in checked if check.importable]

    if invalid or dry_run:
        return MemberImportResponse(
            imported=0 if invalid else len(ready),
            skipped=skipped,
            failed=len(invalid),
            issues=[
                {
                    "row": preview.row,
                    "field": error_fields.get(preview.row),
                    "message": preview.message or "Invalid row",
                }
                for preview in invalid
            ],
            rows=previews,
        )

    importer = _importer(current_user, member_repo, subject_repo, link_repo, outbox)
    results = [await _import_row(row, check, importer, db) for row, check in ready]
    failures = [result for result in results if result.state == "failed"]
    return MemberImportResponse(
        imported=sum(result.state == "imported" for result in results),
        skipped=skipped,
        failed=len(failures),
        issues=[
            {"row": result.row, "field": None, "message": result.message or "Import failed"}
            for result in failures
        ],
        rows=previews,
    )


@router.post("/import/commit", response_model=MemberImportCommitResponse)
@readonly()
async def commit_member_import(
    payload: MemberImportCommitRequest,
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
    """Import a slice of previewed rows, re-checking and committing each one alone.

    The client sends the roster in slices so it can show progress. A row that
    fails is reported and skipped; the rows already written stay written.
    """
    checker = MemberRowChecker(current_user.tenant_id, client_repo, member_repo)
    importer = _importer(current_user, member_repo, subject_repo, link_repo, outbox)
    results: list[MemberImportRowResult] = []
    for entry in payload.rows:
        row = csv_row(entry.row, entry.values)
        check = await checker.check(row)
        results.append(await _import_row(row, check, importer, db))
    return MemberImportCommitResponse(results=results)


def _csv_cell(value: str | None) -> str | None:
    # Spreadsheet applications interpret these prefixes even in quoted CSV cells.
    if isinstance(value, str) and value.lstrip().startswith(("=", "+", "-", "@", "\t", "\r", "\n")):
        return "'" + value
    return value


@router.patch("/{member_id}", response_model=MemberResponse)
@transactional()
async def update_member(
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
    details = updated.model_dump(exclude={"client_id"})
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
    member.update_roster_details(
        **details, coverage_start=member.coverage_start, coverage_end=member.coverage_end
    )
    await member_repo.save(member)
    await record_member_change(
        outbox,
        tenant_id=current_user.tenant_id,
        user_id=current_user.user_id,
        resource_id=member.id.value,
        action="UPDATE",
        operation="Updated",
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


@router.put("/{member_id}/account", response_model=MemberResponse)
@transactional()
async def link_member_account(
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
    await record_member_change(
        outbox,
        tenant_id=current_user.tenant_id,
        user_id=current_user.user_id,
        resource_id=member.id.value,
        action="UPDATE",
        operation="AccountLinked",
    )
    return _response(member)


@router.delete("/{member_id}/account", response_model=MemberResponse)
@transactional()
async def unlink_member_account(
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
    await record_member_change(
        outbox,
        tenant_id=current_user.tenant_id,
        user_id=current_user.user_id,
        resource_id=member.id.value,
        action="UPDATE",
        operation="AccountUnlinked",
    )
    return _response(member)


@router.post("/{member_id}/merge", response_model=MemberMergeResponse)
@transactional()
async def merge_members(
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
    await record_member_change(
        outbox,
        tenant_id=current_user.tenant_id,
        user_id=current_user.user_id,
        resource_id=target.id.value,
        action="UPDATE",
        operation="Merged",
    )
    await record_member_change(
        outbox,
        tenant_id=current_user.tenant_id,
        user_id=current_user.user_id,
        resource_id=source.id.value,
        action="DELETE",
        operation="MergedIntoMember",
    )
    return MemberMergeResponse(
        member=_response(await _get_member(member_id, current_user.tenant_id, member_repo)),
        source_member_id=source.id.value,
        transferred=transferred,
    )


@router.post("/{member_id}/suspend", response_model=MemberResponse)
@transactional()
async def suspend_member(
    member_id: str,
    current_user: TokenData = Depends(require_not_viewer),
    member_repo: EligibleMemberRepository = Depends(get_eligible_member_repository),
    outbox: OutboxRepository = Depends(get_outbox_repository),
    db: AsyncSession = Depends(get_db),
):
    member = await _transition_member(member_id, "suspend", current_user, member_repo)
    await record_member_change(
        outbox,
        tenant_id=current_user.tenant_id,
        user_id=current_user.user_id,
        resource_id=member.id.value,
        action="UPDATE",
        operation="Suspended",
    )
    return _response(member)


@router.post("/{member_id}/reinstate", response_model=MemberResponse)
@transactional()
async def reinstate_member(
    member_id: str,
    current_user: TokenData = Depends(require_not_viewer),
    member_repo: EligibleMemberRepository = Depends(get_eligible_member_repository),
    outbox: OutboxRepository = Depends(get_outbox_repository),
    db: AsyncSession = Depends(get_db),
):
    member = await _transition_member(member_id, "reinstate", current_user, member_repo)
    await record_member_change(
        outbox,
        tenant_id=current_user.tenant_id,
        user_id=current_user.user_id,
        resource_id=member.id.value,
        action="UPDATE",
        operation="Reinstated",
    )
    return _response(member)


@router.post("/{member_id}/terminate", response_model=MemberResponse)
@transactional()
async def terminate_member(
    member_id: str,
    current_user: TokenData = Depends(require_not_viewer),
    member_repo: EligibleMemberRepository = Depends(get_eligible_member_repository),
    outbox: OutboxRepository = Depends(get_outbox_repository),
    db: AsyncSession = Depends(get_db),
):
    member = await _transition_member(member_id, "terminate", current_user, member_repo)
    await record_member_change(
        outbox,
        tenant_id=current_user.tenant_id,
        user_id=current_user.user_id,
        resource_id=member.id.value,
        action="UPDATE",
        operation="Terminated",
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
    member_id: str,
    data: MemberNextOfKinCreate,
    current_user: TokenData = Depends(require_not_viewer),
    member_repo: EligibleMemberRepository = Depends(get_eligible_member_repository),
    next_of_kin_repo: MemberNextOfKinRepository = Depends(get_member_next_of_kin_repository),
    outbox: OutboxRepository = Depends(get_outbox_repository),
    db: AsyncSession = Depends(get_db),
):
    member = await _get_member(member_id, current_user.tenant_id, member_repo)
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
    await record_member_change(
        outbox,
        tenant_id=current_user.tenant_id,
        user_id=current_user.user_id,
        resource_id=contact.id.value,
        member_id=contact.member_id.value,
        action="CREATE",
        operation="Created",
    )
    return _next_of_kin_response(contact)


@router.patch("/{member_id}/next-of-kin/{contact_id}", response_model=MemberNextOfKinResponse)
@transactional()
async def update_member_next_of_kin(
    member_id: str,
    contact_id: str,
    data: MemberNextOfKinUpdate,
    current_user: TokenData = Depends(require_not_viewer),
    member_repo: EligibleMemberRepository = Depends(get_eligible_member_repository),
    next_of_kin_repo: MemberNextOfKinRepository = Depends(get_member_next_of_kin_repository),
    outbox: OutboxRepository = Depends(get_outbox_repository),
    db: AsyncSession = Depends(get_db),
):
    contact = await _get_contact(
        member_id, contact_id, current_user.tenant_id, member_repo, next_of_kin_repo
    )
    contact.update(
        name=data.name.strip(),
        relationship=data.relationship,
        phone=data.phone.strip() if data.phone else None,
        email=Email(str(data.email)) if data.email else None,
        is_primary=data.is_primary,
        now=utc_now(),
    )
    await next_of_kin_repo.save(contact)
    await record_member_change(
        outbox,
        tenant_id=current_user.tenant_id,
        user_id=current_user.user_id,
        resource_id=contact.id.value,
        member_id=contact.member_id.value,
        action="UPDATE",
        operation="Updated",
    )
    return _next_of_kin_response(contact)


@router.delete("/{member_id}/next-of-kin/{contact_id}", status_code=status.HTTP_204_NO_CONTENT)
@transactional()
async def delete_member_next_of_kin(
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
    await record_member_change(
        outbox,
        tenant_id=current_user.tenant_id,
        user_id=current_user.user_id,
        resource_id=contact.id.value,
        member_id=contact.member_id.value,
        action="DELETE",
        operation="Deleted",
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
