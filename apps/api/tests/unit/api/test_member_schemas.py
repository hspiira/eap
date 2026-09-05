import pytest
from pydantic import ValidationError

from app.api.schemas.member_schemas import MemberCreate
from app.domain.enums import MemberRelation


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
