"""Row-level checking and committing for client member roster imports.

The preview and the confirmed import share this module so that a row is judged
by exactly the same rules in both passes. Each committed row is its own unit of
work: the caller commits after every row, so one bad row cannot undo the rows
that already landed.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime

from pydantic import ValidationError

from app.api.schemas.member_schemas import MemberCreate, MemberEmployment
from app.application.use_cases.eligible_member_use_cases import EnrolEligibleMemberUseCase
from app.core.security import TokenData
from app.domain.entities.client import ClientEntity
from app.domain.entities.eligible_member import EligibleMember
from app.domain.entities.member_import import MemberImportRowEntity
from app.domain.enums import EligibilityStatus, MemberGender, MemberImportRowOutcome, MemberRelation
from app.domain.repositories.client_repository import ClientRepository
from app.domain.repositories.eligible_member_repository import EligibleMemberRepository
from app.domain.repositories.outbox_repository import OutboxRepository
from app.domain.value_objects.core import ClientId, EligibleMemberId, Email, TenantId, UserId
from app.domain.value_objects.ids import MemberImportBatchId, MemberImportRowId
from app.shared.handlers.audit_event_handler import AuditEventHandler
from app.shared.utils.member_csv import MemberCsvRow
from app.shared.utils.route_audit_helper import audit_change

DECISIONS = {"import", "skip"}

_OUTCOME_BY_STATE = {
    "new": MemberImportRowOutcome.NEW,
    "duplicate": MemberImportRowOutcome.DUPLICATE,
    "invalid": MemberImportRowOutcome.INVALID,
}


def row_replay_key(row: MemberCsvRow, client_id: ClientId | None, file_hash: str) -> str:
    """A stable key when Staff_ID is present, else one scoped to this exact file and row.

    The fallback lets a blank-Staff_ID row stage without colliding with its
    neighbours in the same file; it does not re-identify the same person
    across a later file, which is a known limitation, not a bug.
    """
    if client_id is not None and row.import_source_id:
        return f"key:{client_id.value}:{row.import_source_id}"
    return f"file:{file_hash}:row:{row.row_number}"


def build_row_entity(
    row: MemberCsvRow,
    check: RowCheck,
    *,
    row_id: MemberImportRowId,
    batch_id: MemberImportBatchId,
    tenant_id: TenantId,
    file_hash: str,
    now: datetime,
) -> MemberImportRowEntity:
    """Turn one checked roster row into the row a batch persists.

    A duplicate or invalid row can never be imported regardless of decision
    (`MemberImportRowEntity.set_decision` enforces this), so its stored
    decision is just a safe default and is never read.
    """
    client_id = check.client.id if check.client else None
    return MemberImportRowEntity(
        id=row_id,
        batch_id=batch_id,
        tenant_id=tenant_id,
        row_number=row.row_number,
        replay_key=row_replay_key(row, client_id, file_hash),
        outcome=_OUTCOME_BY_STATE[check.state],
        decision="import" if check.state == "new" else "skip",
        created_at=now,
        client_code=row.client_code,
        client_id=client_id,
        import_source_id=row.import_source_id,
        staff_number=row.staff_number,
        display_label=row.display_label,
        work_email=row.work_email,
        personal_email=row.personal_email,
        gender=row.gender,
        date_of_birth=row.date_of_birth,
        phone=row.phone,
        national_id=row.national_id,
        passport_number=row.passport_number,
        job_title=row.job_title,
        job_classification=row.job_classification,
        skill=row.skill,
        department=row.department,
        unit=row.unit,
        employment_type=row.employment_type,
        status=row.status,
        relation=row.relation,
        primary_import_source_id=row.primary_import_source_id,
        message=check.message,
    )


def csv_row_from_entity(row: MemberImportRowEntity) -> MemberCsvRow:
    """Rebuild the parser's row shape from a persisted row, for re-checking at apply time."""
    return MemberCsvRow(
        row_number=row.row_number,
        client_code=row.client_code,
        import_source_id=row.import_source_id,
        staff_number=row.staff_number,
        display_label=row.display_label,
        work_email=row.work_email,
        personal_email=row.personal_email,
        gender=row.gender,
        date_of_birth=row.date_of_birth,
        phone=row.phone,
        national_id=row.national_id,
        passport_number=row.passport_number,
        job_title=row.job_title,
        job_classification=row.job_classification,
        skill=row.skill,
        department=row.department,
        unit=row.unit,
        employment_type=row.employment_type,
        status=row.status,
        relation=row.relation,
        primary_import_source_id=row.primary_import_source_id,
    )


@dataclass(frozen=True)
class RowCheck:
    """What one roster row resolves to before anything is written."""

    state: str
    message: str | None = None
    client: ClientEntity | None = None
    data: MemberCreate | None = None

    @property
    def importable(self) -> bool:
        return self.state == "new" and self.data is not None


def _member_create(
    row: MemberCsvRow, client: ClientEntity, *, primary_member_id: str | None
) -> MemberCreate:
    """Build the row's create payload.

    ``employer_member_id`` is deliberately left unset: the member code is
    always issued by the server at commit time, the same as manual creation.
    """
    return MemberCreate(
        client_id=client.id.value,
        import_source_id=row.import_source_id,
        display_label=row.display_label or "",
        work_email=row.work_email,
        personal_email=row.personal_email,
        gender=MemberGender(row.gender.title()) if row.gender else None,
        date_of_birth=date.fromisoformat(row.date_of_birth) if row.date_of_birth else None,
        phone=row.phone,
        staff_number=row.staff_number,
        national_id=row.national_id,
        passport_number=row.passport_number,
        employment=MemberEmployment(
            job_title=row.job_title,
            job_classification=row.job_classification,
            skill=row.skill,
            department=row.department,
            unit=row.unit,
            employment_type=row.employment_type,
        ),
        relation=MemberRelation(row.relation or MemberRelation.EMPLOYEE.value),
        primary_employee_member_id=primary_member_id,
    )


async def issue_member_code(
    member_repo: EligibleMemberRepository,
    *,
    tenant_id: TenantId,
    client_id: ClientId,
    client_code: str,
) -> str:
    """Issue the next ``{client code}-###`` id for this client.

    Shared by manual creation and roster import so every member, no matter
    how they are added or what relation they carry, draws from the same
    per-client sequence.

    Skips codes already taken, so a roster imported with hand-written codes
    under the same prefix continues from the top rather than colliding.

    This sees only committed rows, so it cannot resolve a race between two
    in-flight enrolments. The unique constraint on ``employer_member_id`` is
    what actually guarantees uniqueness; callers turn that violation into a
    409 or a per-row failure, as fits their transport.
    """
    prefix = client_code.strip().upper()
    sequence = await member_repo.next_member_sequence(tenant_id, client_id, prefix)
    for candidate_sequence in range(sequence, sequence + 50):
        candidate = f"{prefix}-{candidate_sequence:03d}"
        existing = await member_repo.find_by_employer_member_id(tenant_id, client_id, candidate)
        if existing is None:
            return candidate
    raise ValueError("Could not issue a member ID for this client")


class MemberRowChecker:
    """Judges roster rows one at a time against the tenant's clients and members.

    An instance remembers the Staff_IDs it has already seen, so a file that
    repeats one inside the same client is caught before either row is written.
    """

    def __init__(
        self,
        tenant_id: str,
        client_repo: ClientRepository,
        member_repo: EligibleMemberRepository,
    ) -> None:
        self._tenant_id = TenantId(tenant_id)
        self._clients = client_repo
        self._members = member_repo
        self._seen: set[tuple[str, str]] = set()

    async def check(
        self,
        row: MemberCsvRow,
        *,
        decision: str | None = None,
        parse_error: str | None = None,
    ) -> RowCheck:
        if parse_error:
            return RowCheck(state="invalid", message=parse_error)
        if decision is not None and decision not in DECISIONS:
            return RowCheck(state="invalid", message="Decision must be import or skip")

        client = (
            await self._clients.get_by_code(self._tenant_id, row.client_code or "")
            if row.client_code
            else None
        )
        if client is None:
            return RowCheck(
                state="invalid",
                message="Company Code does not resolve to a client in this tenant",
            )

        key = (client.id.value, row.import_source_id or "")
        if key in self._seen:
            return RowCheck(
                state="invalid",
                message="Staff_ID is duplicated in this file for this client",
                client=client,
            )
        self._seen.add(key)

        existing = await self._members.find_by_import_source_id(
            self._tenant_id, client.id, row.import_source_id or ""
        )
        if existing is not None:
            if decision not in (None, "skip"):
                return RowCheck(
                    state="invalid",
                    message="Existing members can only be skipped; they are never overwritten",
                    client=client,
                )
            return RowCheck(state="duplicate", client=client)

        primary_member_id = None
        if row.primary_import_source_id:
            primary = await self._members.find_by_import_source_id(
                self._tenant_id, client.id, row.primary_import_source_id
            )
            if primary is None:
                return RowCheck(
                    state="invalid",
                    message="Primary employee's Staff_ID was not found; import the employee first",
                    client=client,
                )
            primary_member_id = primary.id.value

        try:
            data = _member_create(row, client, primary_member_id=primary_member_id)
        except (ValueError, ValidationError) as exc:
            return RowCheck(state="invalid", message=str(exc).split("\n", 1)[-1], client=client)

        if decision == "skip":
            return RowCheck(state="skipped", client=client, data=data)
        return RowCheck(state="new", client=client, data=data)


class MemberRowImporter:
    """Writes one checked row, leaving the transaction boundary to the caller."""

    def __init__(
        self,
        current_user: TokenData,
        use_case: EnrolEligibleMemberUseCase,
        member_repo: EligibleMemberRepository,
        outbox: OutboxRepository,
        tenant_secret: str,
    ) -> None:
        self._user = current_user
        self._use_case = use_case
        self._members = member_repo
        self._outbox = outbox
        self._secret = tenant_secret

    async def enrol(
        self, row: MemberCsvRow, data: MemberCreate, client_code: str
    ) -> EligibleMember:
        tenant_id = TenantId(self._user.tenant_id)
        client_id = ClientId(data.client_id)
        employer_member_id = await issue_member_code(
            self._members,
            tenant_id=tenant_id,
            client_id=client_id,
            client_code=client_code,
        )
        member, _ = await self._use_case.execute(
            tenant_id=tenant_id,
            client_id=client_id,
            employer_member_id=employer_member_id,
            import_source_id=data.import_source_id,
            relation=data.relation,
            tenant_secret=self._secret,
            created_by=UserId(self._user.user_id),
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
        _apply_imported_status(member, row.status)
        member.record_import()
        await self._members.save(member)
        # One row per imported member, as before: the enrolment use case emits
        # the creation and this sends it down the same path the routes use.
        await audit_change(member, AuditEventHandler(self._outbox), self._user)
        return member


#: The source's status word to the transition that reaches it.
_STATUS_TRANSITIONS = {
    EligibilityStatus.ACTIVE.value.casefold(): (
        EligibilityStatus.ACTIVE,
        EligibleMember.reinstate,
    ),
    EligibilityStatus.SUSPENDED.value.casefold(): (
        EligibilityStatus.SUSPENDED,
        EligibleMember.suspend,
    ),
    EligibilityStatus.TERMINATED.value.casefold(): (
        EligibilityStatus.TERMINATED,
        EligibleMember.terminate,
    ),
}


def _apply_imported_status(member: EligibleMember, status: str | None) -> None:
    """Move the new member to the status the source records, if it is not there.

    Enrolment already creates an Active member, so a roster that says Active,
    as a full staff extract does for every row, asked the entity to reinstate
    a member that was never suspended and the domain refused. A transition is
    only run when it changes something.
    """
    wanted = _STATUS_TRANSITIONS.get((status or "Pending").strip().casefold())
    if wanted is None:
        return
    target, transition = wanted
    if member.status is not target:
        transition(member)
