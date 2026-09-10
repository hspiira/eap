"""Row-level checking and committing for client member roster imports.

The preview and the confirmed import share this module so that a row is judged
by exactly the same rules in both passes. Each committed row is its own unit of
work: the caller commits after every row, so one bad row cannot undo the rows
that already landed.
"""

from __future__ import annotations

from copy import deepcopy
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
from app.domain.repositories.member_import_repository import MemberImportRepository
from app.domain.repositories.outbox_repository import OutboxRepository
from app.domain.value_objects.core import ClientId, EligibleMemberId, Email, TenantId, UserId
from app.domain.value_objects.ids import MemberImportBatchId, MemberImportRowId
from app.domain.value_objects.staffing import EmploymentDetails
from app.shared.handlers.audit_event_handler import AuditEventHandler
from app.shared.utils.member_csv import MemberCsvRow, is_employee_relation, parse_roster_date
from app.shared.utils.replay_key import FILE_PREFIX
from app.shared.utils.route_audit_helper import audit_change

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
    return file_scoped_key(file_hash, row.row_number)


def file_scoped_key(file_hash: str, row_number: int) -> str:
    """A key naming one row of one file, claiming no identity."""
    return f"{FILE_PREFIX}{file_hash}:row:{row_number}"


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

    Every row that is not New is staged as "skip". An invalid row can never
    be anything else; a duplicate that matched a member may be moved to
    "update" by a reviewer, but never starts there, so a batch nobody reviews
    writes nothing to an existing member.

    Only a New row's replay key uses the identity form (`key:{client}:{id}`):
    it is the one row actually claiming that Staff_ID. Any other outcome
    falls back to a key scoped to this file and row number instead of also
    computing the identity form, even when the row does carry that Staff_ID.
    The whole point of a Duplicate or Invalid classification is that this row
    is NOT the one holding that key; someone else already does, or another
    row earlier in this same file already claimed it, and reusing that exact
    string collides with whichever row legitimately holds it.
    """
    client_id = check.client.id if check.client else None
    replay_key = (
        row_replay_key(row, client_id, file_hash)
        if check.state == "new"
        else file_scoped_key(file_hash, row.row_number)
    )
    return MemberImportRowEntity(
        id=row_id,
        batch_id=batch_id,
        tenant_id=tenant_id,
        row_number=row.row_number,
        replay_key=replay_key,
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
        date_joined=row.date_joined,
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
        matched_member_id=check.existing.id if check.existing else None,
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
        date_joined=row.date_joined,
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
    """What one roster row resolves to before anything is written.

    `existing` is set only on a duplicate this roster is allowed to update:
    the row's Staff_ID already belongs to that member and nothing in the row
    contradicts them. A duplicate carrying no `existing` cannot be updated,
    and `message` says why.
    """

    state: str
    message: str | None = None
    client: ClientEntity | None = None
    data: MemberCreate | None = None
    existing: EligibleMember | None = None

    @property
    def importable(self) -> bool:
        return self.state == "new" and self.data is not None

    @property
    def updatable(self) -> bool:
        return self.state == "duplicate" and self.existing is not None


#: Member fields a roster row may revise, in the order `update_roster_details`
#: takes them. Identity (client, Staff_ID, member code) and family structure
#: (relation, primary employee) are deliberately absent: see "Decision: a
#: roster row can update the member it matched" in
#: docs/migrations/MEMBERS_MIGRATION.md.
_ROSTER_DETAIL_FIELDS = (
    "display_label",
    "phone",
    "staff_number",
    "national_id",
    "passport_number",
    "work_email",
    "personal_email",
    "gender",
    "date_of_birth",
    "coverage_start",
    "employment",
)

_ROSTER_TEXT_FIELDS = (
    "display_label",
    "phone",
    "staff_number",
    "national_id",
    "passport_number",
)


def _revision(patch: dict[str, object], name: str, value: object, current: object) -> None:
    """Record `value` as a change to `name`, unless the roster left it blank."""
    if value is not None and value != current:
        patch[name] = value


def _merged_employment(
    row: MemberCsvRow, current: EmploymentDetails | None
) -> EmploymentDetails | None:
    """The roster's employment values laid over the member's, field by field."""
    merged = {
        name: getattr(row, name) or (getattr(current, name, None) if current else None)
        for name in EmploymentDetails.__dataclass_fields__
    }
    return EmploymentDetails.build(**merged)


def _roster_date(value: str | None) -> date | None:
    return parse_roster_date(value) if value else None


def roster_patch(row: MemberCsvRow, member: EligibleMember) -> dict[str, object]:
    """The member fields this roster row would revise.

    A blank cell asserts nothing about the member and leaves the stored value
    alone; only a value the roster actually carries can overwrite one. An
    import can therefore add and correct, but never clear: emptying a field
    stays an explicit act on the member's own record.

    Raises ValueError when a cell the roster did fill cannot be read.
    """
    patch: dict[str, object] = {}
    for name in _ROSTER_TEXT_FIELDS:
        _revision(patch, name, getattr(row, name), getattr(member, name))
    for name in ("work_email", "personal_email"):
        raw = getattr(row, name)
        _revision(patch, name, Email(raw) if raw else None, getattr(member, name))
    _revision(
        patch, "gender", MemberGender(row.gender.title()) if row.gender else None, member.gender
    )
    _revision(patch, "date_of_birth", _roster_date(row.date_of_birth), member.date_of_birth)
    _revision(patch, "coverage_start", _roster_date(row.date_joined), member.coverage_start)
    _revision(patch, "employment", _merged_employment(row, member.employment), member.employment)
    return patch


def update_blocked(row: MemberCsvRow, member: EligibleMember) -> str | None:
    """Why this row cannot revise the member it matched, or None when it can.

    A contradicting Relation refuses the whole row rather than quietly
    revising everything except the relationship: moving a member between
    Employee and dependant carries invariants a per-row apply loop cannot
    settle (an employee's beneficiaries have to be reassigned first), and
    silently ignoring a column the roster did fill is the worse failure.
    """
    try:
        relation = MemberRelation(row.relation) if row.relation else member.relation
    except ValueError:
        return f"Relation '{row.relation}' is not a relationship this system records"
    if relation is not member.relation:
        return (
            f"This roster says {relation.value} but the member is recorded as "
            f"{member.relation.value}; change the relationship on the member record first"
        )
    try:
        roster_patch(row, member)
    except ValueError as exc:
        return str(exc)
    return None


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
        date_of_birth=parse_roster_date(row.date_of_birth) if row.date_of_birth else None,
        coverage_start=parse_roster_date(row.date_joined) if row.date_joined else None,
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

    Every per-row lookup (client, existing member, staged-elsewhere row) is
    memoized on this instance, so a caller processing a whole file should
    call `preload()` once first: it fills these same caches with a handful
    of batched queries instead of leaving `check()` to make one query per
    row. Without it, staging thousands of rows one at a time was slow enough
    to time out a serverless function; `preload()` is optional exactly so
    `apply`'s per-row re-check, which needs live data rather than a bulk
    snapshot, can keep calling `check()` without it and still benefit from
    caching within its own run (e.g. several dependants sharing one primary).
    """

    def __init__(
        self,
        tenant_id: str,
        client_repo: ClientRepository,
        member_repo: EligibleMemberRepository,
        imports_repo: MemberImportRepository,
    ) -> None:
        self._tenant_id = TenantId(tenant_id)
        self._clients = client_repo
        self._members = member_repo
        self._imports = imports_repo
        self._seen: set[tuple[str, str]] = set()
        self._clients_by_code: dict[str, ClientEntity | None] = {}
        self._members_by_id: dict[tuple[str, str], EligibleMember | None] = {}
        self._staged_rows_by_key: dict[str, MemberImportRowEntity | None] = {}

    async def preload(self, rows: list[MemberCsvRow], file_hash: str | None) -> None:
        """Batch every lookup `check()` would otherwise repeat once per row."""
        for code in {row.client_code for row in rows if row.client_code}:
            self._clients_by_code.setdefault(
                code, await self._clients.get_by_code(self._tenant_id, code)
            )

        wanted_by_client: dict[str, set[str]] = {}
        for row in rows:
            client = self._clients_by_code.get(row.client_code or "")
            if client is None:
                continue
            wanted = wanted_by_client.setdefault(client.id.value, set())
            if row.import_source_id:
                wanted.add(row.import_source_id)
            if row.primary_import_source_id:
                wanted.add(row.primary_import_source_id)
        for client_id_value, ids in wanted_by_client.items():
            found = await self._members.find_by_import_source_ids(
                self._tenant_id, ClientId(client_id_value), sorted(ids)
            )
            for import_id in ids:
                self._members_by_id.setdefault((client_id_value, import_id), found.get(import_id))

        if file_hash is None:
            return
        keys = {
            row_replay_key(row, client.id, file_hash)
            for row in rows
            if row.import_source_id
            and (client := self._clients_by_code.get(row.client_code or "")) is not None
        }
        if not keys:
            return
        found_rows = await self._imports.find_rows_by_replay_keys(self._tenant_id, sorted(keys))
        for key in keys:
            self._staged_rows_by_key.setdefault(key, found_rows.get(key))

    async def check(
        self,
        row: MemberCsvRow,
        *,
        parse_error: str | None = None,
        file_hash: str | None = None,
    ) -> RowCheck:
        if parse_error:
            return RowCheck(state="invalid", message=parse_error)

        client = await self._client_for(row)
        if client is None:
            return RowCheck(
                state="invalid",
                message="Company Code does not resolve to a client in this tenant",
            )

        repeated = self._claim_staff_id(client, row)
        if repeated:
            return repeated

        enrolled = await self._already_enrolled(client, row)
        if enrolled:
            return enrolled

        if file_hash is not None:
            staged_elsewhere = await self._already_staged_elsewhere(client, row, file_hash)
            if staged_elsewhere:
                return staged_elsewhere

        primary_member_id, unresolved = await self._primary_member_id(client, row)
        if unresolved:
            return unresolved

        return self._checked(row, client, primary_member_id)

    async def _client_for(self, row: MemberCsvRow) -> ClientEntity | None:
        if not row.client_code:
            return None
        if row.client_code not in self._clients_by_code:
            self._clients_by_code[row.client_code] = await self._clients.get_by_code(
                self._tenant_id, row.client_code
            )
        return self._clients_by_code[row.client_code]

    async def _member_by_import_id(
        self, client: ClientEntity, import_source_id: str
    ) -> EligibleMember | None:
        """Cached per (client, id): `preload()` fills these in bulk; a miss falls back to one query."""
        key = (client.id.value, import_source_id)
        if key not in self._members_by_id:
            self._members_by_id[key] = await self._members.find_by_import_source_id(
                self._tenant_id, client.id, import_source_id
            )
        return self._members_by_id[key]

    def _claim_staff_id(self, client: ClientEntity, row: MemberCsvRow) -> RowCheck | None:
        """Records the row's Staff_ID, rejecting a second use of it in the same file.

        A blank Staff_ID (a dependant, now that one is allowed to have none)
        claims nothing: two dependants sharing no ID are not a repeat of the
        same person, so blank never collides with itself here.
        """
        if not row.import_source_id:
            return None
        key = (client.id.value, row.import_source_id)
        if key in self._seen:
            return RowCheck(
                state="invalid",
                message="Staff_ID is duplicated in this file for this client",
                client=client,
            )
        self._seen.add(key)
        return None

    async def _already_enrolled(self, client: ClientEntity, row: MemberCsvRow) -> RowCheck | None:
        """Whether this row's own Staff_ID already belongs to a real member.

        A dependant with no Staff_ID of their own claims nothing here; they
        are identified by Primary Staff ID instead, checked separately.

        The member comes back on the check so a reviewer can choose to revise
        them from this row. It is withheld, with the reason, when the row
        contradicts the member it matched: the row is then a duplicate that
        can only be skipped, as every duplicate once was.
        """
        if not row.import_source_id:
            return None
        existing = await self._member_by_import_id(client, row.import_source_id)
        if existing is None:
            return None
        blocked = update_blocked(row, existing)
        if blocked:
            return RowCheck(state="duplicate", message=blocked, client=client)
        return RowCheck(state="duplicate", client=client, existing=existing)

    async def _already_staged_elsewhere(
        self, client: ClientEntity, row: MemberCsvRow, file_hash: str
    ) -> RowCheck | None:
        """A live row in another batch already claims this Staff_ID's replay key.

        `_claim_staff_id` only catches a repeat within this same file; a batch
        left Staged from an earlier, unrelated upload holds its rows' keys
        until it is applied or abandoned. Without this check, staging a
        second roster that overlaps with one still claims the same
        (tenant_id, replay_key) the first insert took, and the whole bulk
        insert for this file fails with an unhandled IntegrityError instead
        of classifying the one row that collides.
        """
        if not row.import_source_id:
            return None
        key = row_replay_key(row, client.id, file_hash)
        if key not in self._staged_rows_by_key:
            self._staged_rows_by_key[key] = await self._imports.find_row_by_replay_key(
                self._tenant_id, key
            )
        existing = self._staged_rows_by_key[key]
        if existing is None:
            return None
        return RowCheck(
            state="duplicate",
            message=f"Already staged as row {existing.row_number} of batch {existing.batch_id.value}",
            client=client,
        )

    async def _primary_member_id(
        self, client: ClientEntity, row: MemberCsvRow
    ) -> tuple[str | None, RowCheck | None]:
        """The beneficiary's primary employee, or the rejection when it is not on file yet."""
        if not row.primary_import_source_id:
            if is_employee_relation(row.relation):
                return None, None
            return None, RowCheck(
                state="invalid",
                message="Primary Staff ID is required for a beneficiary",
                client=client,
            )
        primary = await self._member_by_import_id(client, row.primary_import_source_id)
        if primary is None:
            return None, RowCheck(
                state="invalid",
                message="Primary employee's Staff_ID was not found; import the employee first",
                client=client,
            )
        return primary.id.value, None

    def _checked(
        self, row: MemberCsvRow, client: ClientEntity, primary_member_id: str | None
    ) -> RowCheck:
        try:
            data = _member_create(row, client, primary_member_id=primary_member_id)
        except (ValueError, ValidationError) as exc:
            return RowCheck(state="invalid", message=str(exc).split("\n", 1)[-1], client=client)
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
            employment=EmploymentDetails.build(**data.employment.model_dump())
            if data.employment
            else None,
            coverage_start=data.coverage_start,
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


def _apply_imported_status(member: EligibleMember, status: str | None) -> bool:
    """Move the member to the status the source records. True when it moved.

    Enrolment already creates an Active member, so a roster that says Active,
    as a full staff extract does for every row, asked the entity to reinstate
    a member that was never suspended and the domain refused. A transition is
    only run when it changes something.
    """
    wanted = _STATUS_TRANSITIONS.get((status or "Pending").strip().casefold())
    if wanted is None:
        return False
    target, transition = wanted
    if member.status is target:
        return False
    transition(member)
    return True


class MemberRowUpdater:
    """Revises the member one roster row matched, leaving the transaction to the caller."""

    def __init__(
        self,
        current_user: TokenData,
        member_repo: EligibleMemberRepository,
        outbox: OutboxRepository,
    ) -> None:
        self._user = current_user
        self._members = member_repo
        self._outbox = outbox

    async def update(self, row: MemberCsvRow, member: EligibleMember) -> bool:
        """Write the roster's non-blank values onto `member`. False when nothing changed.

        A row whose every value the member already carries writes nothing at
        all, so re-uploading an unchanged roster leaves no audit trail of
        edits that did not happen.
        """
        patch = roster_patch(row, member)
        before = deepcopy(member)
        if patch:
            _apply_roster_patch(member, patch)
        moved = _apply_imported_status(member, row.status)
        if not patch and not moved:
            return False
        member.record_import()
        await self._members.save(member)
        await audit_change(member, AuditEventHandler(self._outbox), self._user, old_entity=before)
        return True


def _apply_roster_patch(member: EligibleMember, patch: dict[str, object]) -> None:
    """Re-state the member's roster details with the patch laid over them.

    `update_roster_details` assigns every field it takes, so an unpatched one
    has to be passed back as it stands or it would be cleared.
    """
    details = {name: patch.get(name, getattr(member, name)) for name in _ROSTER_DETAIL_FIELDS}
    member.update_roster_details(
        employer_member_id=member.employer_member_id,
        relation=member.relation,
        primary_employee_member_id=member.primary_employee_member_id,
        coverage_end=member.coverage_end,
        **details,  # type: ignore[arg-type]
    )
