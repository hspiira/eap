"""Optional employment details carried on the member roster."""

from datetime import UTC, datetime

import pytest

from app.domain.entities.eligible_member import EligibleMember
from app.domain.enums import EligibilityStatus, MemberRelation
from app.domain.value_objects.core import ClientId, EligibleMemberId, TenantId
from app.domain.value_objects.staffing import (
    EMPLOYMENT_DETAIL_MAX_LENGTH,
    EmploymentDetails,
)


def _member(employment: EmploymentDetails | None = None) -> EligibleMember:
    now = datetime.now(UTC)
    return EligibleMember(
        id=EligibleMemberId("em-1"),
        tenant_id=TenantId("t-1"),
        client_id=ClientId("client-1"),
        employer_member_id="HR-1",
        relation=MemberRelation.EMPLOYEE,
        status=EligibilityStatus.ACTIVE,
        employment=employment,
        created_at=now,
        updated_at=now,
    )


class TestEmploymentDetails:
    def test_blank_and_whitespace_values_normalise_to_none(self):
        details = EmploymentDetails(department="  Treasury  ", unit="   ", skill="")
        assert details.department == "Treasury"
        assert details.unit is None
        assert details.skill is None

    def test_build_returns_none_when_the_employer_supplied_nothing(self):
        assert EmploymentDetails.build() is None
        assert EmploymentDetails.build(job_title=None, unit="  ") is None

    def test_build_returns_the_details_when_any_value_is_present(self):
        details = EmploymentDetails.build(employment_type="FTC")
        assert details is not None
        assert details.employment_type == "FTC"

    def test_is_empty_distinguishes_a_populated_block(self):
        assert EmploymentDetails().is_empty is True
        assert EmploymentDetails(unit="SME Banking").is_empty is False

    def test_a_value_longer_than_the_column_is_rejected(self):
        with pytest.raises(ValueError, match="exceeds"):
            EmploymentDetails(unit="x" * (EMPLOYMENT_DETAIL_MAX_LENGTH + 1))

    def test_a_non_string_value_is_rejected(self):
        with pytest.raises(ValueError, match="must be a string"):
            EmploymentDetails(department=17)  # type: ignore[arg-type]


class TestMemberEmployment:
    def test_a_member_carries_no_employment_by_default(self):
        assert _member().employment is None

    def test_a_roster_update_sets_the_details(self):
        member = _member()
        member.update_roster_details(
            employer_member_id="HR-1",
            relation=MemberRelation.EMPLOYEE,
            employment=EmploymentDetails(department="Legal", unit="Kampala Road branch"),
        )
        assert member.employment is not None
        assert member.employment.department == "Legal"
        assert member.employment.unit == "Kampala Road branch"

    def test_a_roster_update_clears_details_the_employer_stopped_sending(self):
        member = _member(EmploymentDetails(department="Legal"))
        member.update_roster_details(
            employer_member_id="HR-1",
            relation=MemberRelation.EMPLOYEE,
            employment=None,
        )
        assert member.employment is None

    def test_an_all_blank_block_is_stored_as_no_details(self):
        member = _member(EmploymentDetails(department="Legal"))
        member.update_roster_details(
            employer_member_id="HR-1",
            relation=MemberRelation.EMPLOYEE,
            employment=EmploymentDetails(),
        )
        assert member.employment is None

    def test_employment_does_not_affect_eligibility(self):
        """No domain rule reads these fields; they are record and segmentation only."""
        bare = _member()
        described = _member(EmploymentDetails(department="Legal", employment_type="FTC"))
        assert bare.is_currently_eligible() == described.is_currently_eligible()
