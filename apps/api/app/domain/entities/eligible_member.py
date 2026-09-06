"""Eligible member aggregate.

The HR-known view of one EAP-eligible person. Carries the employer's HRIS
identifier and the relationship to the primary employee. Operational service
sessions reference the member directly. Clinical cases and notes stay behind
the pseudonymous ``EligibleMemberClinicalLink`` boundary.
"""

from dataclasses import dataclass, field
from datetime import date, datetime

from app.domain.enums import EligibilityStatus, MemberGender, MemberRelation
from app.domain.events import DomainEvent
from app.domain.exceptions import DomainError, InvalidStateError
from app.domain.value_objects.core import (
    ClientId,
    EligibleMemberId,
    Email,
    TenantId,
    UserId,
)
from app.shared.utils.datetime import utc_now


@dataclass
class EligibleMember:
    id: EligibleMemberId
    tenant_id: TenantId
    client_id: ClientId
    employer_member_id: str
    relation: MemberRelation
    status: EligibilityStatus
    created_at: datetime
    updated_at: datetime
    primary_employee_member_id: EligibleMemberId | None = None
    coverage_start: date | None = None
    coverage_end: date | None = None
    work_email: Email | None = None
    personal_email: Email | None = None
    display_label: str | None = None
    date_of_birth: date | None = None
    gender: MemberGender | None = None
    phone: str | None = None
    staff_number: str | None = None
    national_id: str | None = None
    passport_number: str | None = None
    last_imported_at: datetime | None = None
    suspended_at: datetime | None = None
    terminated_at: datetime | None = None
    created_by: UserId | None = None
    user_id: UserId | None = None
    events: list[DomainEvent] = field(default_factory=list[DomainEvent])

    def link_account(self, user_id: UserId) -> None:
        if self.user_id == user_id:
            return
        if self.user_id is not None:
            raise InvalidStateError("Member already has a linked account")
        self.user_id = user_id
        self.updated_at = utc_now()

    def unlink_account(self) -> None:
        if self.user_id is None:
            return
        self.user_id = None
        self.updated_at = utc_now()

    def __post_init__(self) -> None:
        if not self.employer_member_id.strip():
            raise DomainError("EligibleMember requires an employer_member_id")
        if self.coverage_end and self.coverage_start and self.coverage_end < self.coverage_start:
            raise DomainError("coverage_end must be on or after coverage_start")
        if self.relation != MemberRelation.EMPLOYEE and self.primary_employee_member_id is None:
            raise DomainError(f"{self.relation.value} requires a primary_employee_member_id")
        if self.relation == MemberRelation.EMPLOYEE and self.primary_employee_member_id is not None:
            raise DomainError("Employees cannot have a primary employee member")
        if self.primary_employee_member_id == self.id:
            raise DomainError("A member cannot be their own primary employee")

    def suspend(self, now: datetime | None = None) -> None:
        if self.status == EligibilityStatus.TERMINATED:
            raise InvalidStateError("Cannot suspend a terminated member")
        if self.status == EligibilityStatus.SUSPENDED:
            return
        now = now or utc_now()
        self.status = EligibilityStatus.SUSPENDED
        self.suspended_at = now
        self.updated_at = now

    def reinstate(self, now: datetime | None = None) -> None:
        if self.status not in {
            EligibilityStatus.SUSPENDED,
            EligibilityStatus.PENDING,
        }:
            raise InvalidStateError(f"Cannot reinstate a {self.status.value} member")
        now = now or utc_now()
        self.status = EligibilityStatus.ACTIVE
        self.suspended_at = None
        self.updated_at = now

    def terminate(self, *, end_date: date | None = None, now: datetime | None = None) -> None:
        if self.status == EligibilityStatus.TERMINATED:
            return
        now = now or utc_now()
        self.status = EligibilityStatus.TERMINATED
        self.terminated_at = now
        self.coverage_end = end_date or now.date()
        self.updated_at = now

    def record_import(self, *, when: datetime | None = None) -> None:
        self.last_imported_at = when or utc_now()
        self.updated_at = self.last_imported_at

    def update_roster_details(
        self,
        *,
        employer_member_id: str,
        relation: MemberRelation,
        primary_employee_member_id: EligibleMemberId | None = None,
        coverage_start: date | None = None,
        coverage_end: date | None = None,
        work_email: Email | None = None,
        personal_email: Email | None = None,
        display_label: str | None = None,
        date_of_birth: date | None = None,
        gender: MemberGender | None = None,
        phone: str | None = None,
        staff_number: str | None = None,
        national_id: str | None = None,
        passport_number: str | None = None,
    ) -> None:
        """Update current roster details without creating a User account."""
        if not employer_member_id.strip():
            raise DomainError("EligibleMember requires an employer_member_id")
        if coverage_end and coverage_start and coverage_end < coverage_start:
            raise DomainError("coverage_end must be on or after coverage_start")
        if relation == MemberRelation.EMPLOYEE and primary_employee_member_id is not None:
            raise DomainError("Employees cannot have a primary employee member")
        if relation != MemberRelation.EMPLOYEE and primary_employee_member_id is None:
            raise DomainError(f"{relation.value} requires a primary_employee_member_id")
        if primary_employee_member_id == self.id:
            raise DomainError("A member cannot be their own primary employee")

        self.employer_member_id = employer_member_id
        self.relation = relation
        self.primary_employee_member_id = primary_employee_member_id
        self.coverage_start = coverage_start
        self.coverage_end = coverage_end
        self.work_email = work_email
        self.personal_email = personal_email
        self.display_label = display_label
        self.date_of_birth = date_of_birth
        self.gender = gender
        self.phone = phone
        self.staff_number = staff_number
        self.national_id = national_id
        self.passport_number = passport_number
        self.updated_at = utc_now()

    def is_currently_eligible(self, *, today: date | None = None) -> bool:
        today = today or utc_now().date()
        if self.status != EligibilityStatus.ACTIVE:
            return False
        if self.coverage_start and self.coverage_start > today:
            return False
        if self.coverage_end and self.coverage_end < today:
            return False
        return True
