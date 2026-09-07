"""Row-level checking and committing for client member roster imports.

The preview and the confirmed import share this module so that a row is judged
by exactly the same rules in both passes. Each committed row is its own unit of
work: the caller commits after every row, so one bad row cannot undo the rows
that already landed.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date

from pydantic import ValidationError

from app.api.schemas.member_schemas import MemberCreate, MemberImportRowValues
from app.application.services.member_audit import record_member_change
from app.application.use_cases.eligible_member_use_cases import EnrolEligibleMemberUseCase
from app.core.security import TokenData
from app.domain.entities.client import ClientEntity
from app.domain.entities.eligible_member import EligibleMember
from app.domain.enums import EligibilityStatus, MemberGender, MemberRelation
from app.domain.repositories.client_repository import ClientRepository
from app.domain.repositories.eligible_member_repository import EligibleMemberRepository
from app.domain.repositories.outbox_repository import OutboxRepository
from app.domain.value_objects.core import ClientId, EligibleMemberId, Email, TenantId, UserId
from app.shared.utils.member_csv import MemberCsvRow

DECISIONS = {"import", "skip"}


def row_values(row: MemberCsvRow) -> MemberImportRowValues:
    return MemberImportRowValues(
        client_code=row.client_code,
        employer_member_id=row.employer_member_id,
        staff_number=row.staff_number,
        display_label=row.display_label,
        work_email=row.work_email,
        personal_email=row.personal_email,
        gender=row.gender,
        date_of_birth=row.date_of_birth,
        phone=row.phone,
        national_id=row.national_id,
        passport_number=row.passport_number,
        status=row.status,
        relation=row.relation,
        primary_employee_member_id=row.primary_employee_member_id,
    )


def csv_row(row_number: int, values: MemberImportRowValues) -> MemberCsvRow:
    return MemberCsvRow(row_number=row_number, **values.model_dump())


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


def _member_create(row: MemberCsvRow, client: ClientEntity) -> MemberCreate:
    return MemberCreate(
        client_id=client.id.value,
        employer_member_id=row.employer_member_id,
        display_label=row.display_label or "",
        work_email=row.work_email,
        personal_email=row.personal_email,
        gender=MemberGender(row.gender.title()) if row.gender else None,
        date_of_birth=date.fromisoformat(row.date_of_birth) if row.date_of_birth else None,
        phone=row.phone,
        staff_number=row.staff_number,
        national_id=row.national_id,
        passport_number=row.passport_number,
        relation=MemberRelation(row.relation or MemberRelation.EMPLOYEE.value),
        primary_employee_member_id=row.primary_employee_member_id,
    )


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

        key = (client.id.value, row.employer_member_id or "")
        if key in self._seen:
            return RowCheck(
                state="invalid",
                message="Staff_ID is duplicated in this file for this client",
                client=client,
            )
        self._seen.add(key)

        existing = await self._members.find_by_employer_member_id(
            self._tenant_id, client.id, row.employer_member_id or ""
        )
        if existing is not None:
            if decision not in (None, "skip"):
                return RowCheck(
                    state="invalid",
                    message="Existing members can only be skipped; they are never overwritten",
                    client=client,
                )
            return RowCheck(state="duplicate", client=client)

        try:
            data = _member_create(row, client)
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

    async def enrol(self, row: MemberCsvRow, data: MemberCreate) -> EligibleMember:
        member, _ = await self._use_case.execute(
            tenant_id=TenantId(self._user.tenant_id),
            client_id=ClientId(data.client_id),
            employer_member_id=row.employer_member_id or "",
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
        await record_member_change(
            self._outbox,
            tenant_id=self._user.tenant_id,
            user_id=self._user.user_id,
            resource_id=member.id.value,
            action="CREATE",
            operation="Imported",
        )
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
