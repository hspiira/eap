"""What a roster row is allowed to change about a member it already created.

The rule these pin: a blank cell asserts nothing and leaves the stored value
alone, so an import adds and corrects but never clears. Recorded as "Decision:
a roster row can update the member it matched" in
docs/migrations/MEMBERS_MIGRATION.md.
"""

from datetime import date

import pytest

from app.api.services.member_import import roster_patch, update_blocked
from app.domain.entities.eligible_member import EligibleMember
from app.domain.enums import EligibilityStatus, MemberGender, MemberRelation
from app.domain.value_objects.core import ClientId, EligibleMemberId, Email, TenantId
from app.domain.value_objects.staffing import EmploymentDetails
from app.shared.utils.datetime import utc_now
from app.shared.utils.member_csv import MemberCsvRow

_BLANK = dict.fromkeys(MemberCsvRow.__dataclass_fields__, None)


def row(**overrides) -> MemberCsvRow:
    return MemberCsvRow(**{**_BLANK, "row_number": 2, "display_label": "Amina", **overrides})


def member(**overrides) -> EligibleMember:
    now = utc_now()
    return EligibleMember(
        **{
            "id": EligibleMemberId("m1"),
            "tenant_id": TenantId("t1"),
            "client_id": ClientId("c1"),
            "employer_member_id": "ACM-001",
            "display_label": "Amina",
            "relation": MemberRelation.EMPLOYEE,
            "status": EligibilityStatus.ACTIVE,
            "created_at": now,
            "updated_at": now,
            **overrides,
        }
    )


class TestBlankLeavesTheStoredValueAlone:
    @pytest.mark.parametrize(
        ("field", "stored"),
        [
            ("phone", "0700111222"),
            ("staff_number", "1001"),
            ("national_id", "CF123456"),
            ("passport_number", "B0123456"),
            ("display_label", "Amina"),
        ],
    )
    def test_a_blank_text_cell_is_not_a_change(self, field, stored):
        assert roster_patch(row(), member(**{field: stored})) == {}

    def test_a_blank_email_cell_is_not_a_change(self):
        stored = member(work_email=Email("amina@acme.com"))
        assert roster_patch(row(), stored) == {}

    def test_a_blank_date_of_birth_is_not_a_change(self):
        assert roster_patch(row(), member(date_of_birth=date(1990, 4, 3))) == {}

    def test_a_blank_date_joined_is_not_a_change(self):
        assert roster_patch(row(), member(coverage_start=date(2024, 1, 15))) == {}

    def test_a_blank_gender_is_not_a_change(self):
        assert roster_patch(row(), member(gender=MemberGender.FEMALE)) == {}

    def test_a_roster_with_no_employment_columns_keeps_the_stored_details(self):
        stored = EmploymentDetails(job_title="Teller", department="Operations")
        assert roster_patch(row(), member(employment=stored)) == {}


class TestAValueTheRosterCarries:
    def test_a_differing_value_is_a_change(self):
        assert roster_patch(row(phone="0700111222"), member()) == {"phone": "0700111222"}

    def test_a_value_the_member_already_has_is_not_a_change(self):
        assert roster_patch(row(phone="0700111222"), member(phone="0700111222")) == {}

    def test_an_email_is_normalised_before_it_is_compared(self):
        stored = member(work_email=Email("amina@acme.com"))
        assert roster_patch(row(work_email="Amina@ACME.com"), stored) == {}

    def test_a_day_first_date_of_birth_is_read_the_same_way_as_on_import(self):
        patch = roster_patch(row(date_of_birth="03/04/1990"), member())
        assert patch == {"date_of_birth": date(1990, 4, 3)}

    def test_date_joined_revises_coverage_start(self):
        patch = roster_patch(row(date_joined="15/01/2024"), member())
        assert patch == {"coverage_start": date(2024, 1, 15)}

    def test_gender_is_read_case_insensitively(self):
        assert roster_patch(row(gender="female"), member()) == {"gender": MemberGender.FEMALE}


class TestEmployment:
    def test_a_supplied_column_does_not_wipe_the_columns_beside_it(self):
        stored = EmploymentDetails(job_title="Teller", department="Operations")
        patch = roster_patch(row(job_title="Branch Manager"), member(employment=stored))
        assert patch["employment"] == EmploymentDetails(
            job_title="Branch Manager", department="Operations"
        )

    def test_a_member_with_no_employment_yet_takes_what_the_roster_gives(self):
        patch = roster_patch(row(department="Operations"), member())
        assert patch["employment"] == EmploymentDetails(department="Operations")


class TestUpdateBlocked:
    def test_a_row_that_matches_the_member_is_allowed(self):
        assert update_blocked(row(phone="0700111222"), member()) is None

    def test_a_blank_relation_takes_no_position_on_the_relationship(self):
        """Blank means "no opinion", not "Employee"; a dependant stays updatable."""
        dependant = member(
            relation=MemberRelation.SPOUSE,
            primary_employee_member_id=EligibleMemberId("m2"),
        )
        assert update_blocked(row(), dependant) is None

    def test_a_contradicting_relation_refuses_the_whole_row(self):
        blocked = update_blocked(row(relation="Spouse"), member())
        assert blocked is not None
        assert "Spouse" in blocked
        assert "Employee" in blocked

    def test_an_unknown_relation_is_refused_rather_than_guessed_at(self):
        blocked = update_blocked(row(relation="Cousin"), member())
        assert blocked is not None
        assert "Cousin" in blocked

    @pytest.mark.parametrize(
        "bad",
        [
            {"date_of_birth": "not a date"},
            {"date_joined": "31/02/2024"},
            {"work_email": "not-an-email"},
            {"gender": "Unspecified"},
        ],
    )
    def test_a_value_that_cannot_be_read_refuses_the_row(self, bad):
        assert update_blocked(row(**bad), member()) is not None
