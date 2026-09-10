from datetime import date, timedelta

import pytest
from pydantic import ValidationError

from app.api.schemas.member_schemas import MemberCreate, MemberNextOfKinCreate, MemberUpdate
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


def test_next_of_kin_requires_name_and_contact_method():
    with pytest.raises(ValidationError, match="phone or email"):
        MemberNextOfKinCreate(
            name="Jane Doe",
            relationship="Spouse",
        )

    with pytest.raises(ValidationError, match="name"):
        MemberNextOfKinCreate(
            name=" ",
            relationship="Spouse",
            phone="+256700000000",
        )


def test_next_of_kin_accepts_phone_or_email():
    contact = MemberNextOfKinCreate(
        name="Jane Doe",
        relationship="Spouse",
        email="jane@example.com",
        is_primary=True,
    )
    assert contact.email == "jane@example.com"
    assert contact.is_primary is True


def test_employment_details_are_optional_on_create():
    member = MemberCreate(
        client_id="client-1",
        employer_member_id="HR-1",
        relation=MemberRelation.EMPLOYEE,
        display_label="Amina Namukasa",
    )
    assert member.employment is None


def test_employment_details_are_accepted_on_create():
    member = MemberCreate(
        client_id="client-1",
        employer_member_id="HR-1",
        relation=MemberRelation.EMPLOYEE,
        display_label="Amina Namukasa",
        employment={
            "job_title": "Branch Manager",
            "job_classification": "Manager",
            "skill": "Officer",
            "department": "Operations",
            "unit": "Kampala Road branch",
            "employment_type": "Permanent",
        },
    )
    assert member.employment is not None
    assert member.employment.department == "Operations"
    assert member.employment.employment_type == "Permanent"


def test_employment_details_can_be_patched():
    patch = MemberUpdate(employment={"department": "Treasury"})
    assert patch.employment is not None
    assert patch.employment.department == "Treasury"
    assert patch.employment.unit is None


def test_an_unknown_employment_field_is_rejected():
    with pytest.raises(ValidationError):
        MemberUpdate(employment={"cost_centre": "CC-1"})


def test_an_over_long_employment_value_is_rejected():
    with pytest.raises(ValidationError):
        MemberUpdate(employment={"unit": "x" * 256})
