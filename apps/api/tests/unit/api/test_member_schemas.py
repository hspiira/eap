from datetime import date, timedelta

import pytest
from pydantic import ValidationError

from app.api.schemas.member_schemas import MemberCreate, MemberUpdate
from app.domain.enums import MemberGender, MemberRelation


def test_member_name_is_required():
    with pytest.raises(ValidationError, match="display_label"):
        MemberCreate(
            client_id="client-1",
            employer_member_id="HR-1",
            relation=MemberRelation.EMPLOYEE,
        )


def test_member_name_cannot_be_blank():
    with pytest.raises(ValidationError, match="display_label"):
        MemberCreate(
            client_id="client-1",
            employer_member_id="HR-1",
            relation=MemberRelation.EMPLOYEE,
            display_label="   ",
        )


def test_member_profile_fields_are_supported():
    member = MemberCreate(
        client_id="client-1",
        employer_member_id="HR-1",
        relation=MemberRelation.EMPLOYEE,
        display_label="Amina Namukasa",
        date_of_birth=date(1990, 1, 15),
        gender=MemberGender.FEMALE,
        phone="+256700000000",
    )
    assert member.date_of_birth == date(1990, 1, 15)
    assert member.gender == MemberGender.FEMALE
    assert member.phone == "+256700000000"


def test_member_date_of_birth_cannot_be_in_the_future():
    with pytest.raises(ValidationError, match="future"):
        MemberUpdate(date_of_birth=date.today() + timedelta(days=1))
