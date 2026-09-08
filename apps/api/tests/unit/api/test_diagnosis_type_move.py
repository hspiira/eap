"""A diagnosis may be moved between types, but not onto a type nobody can see.

``list_types`` returns a type only when ``is_active`` is true and
``effective_until`` is null. A move onto a type failing either condition would
report success and take the diagnosis out of every picker, so the route refuses
it rather than letting the tree lose a leaf silently.
"""

import pytest
from fastapi import HTTPException

from app.api.routes.diagnoses import _assert_available_type
from app.domain.entities.diagnosis import DiagnosisType


def _type(*, is_active: bool = True, effective_until=None) -> DiagnosisType:
    return DiagnosisType(
        id="t_career",
        code="CAREER_CHALLENGES",
        name="Career Challenges",
        description=None,
        sort_order=0,
        is_active=is_active,
        version=1,
        effective_until=effective_until,
    )


class _Repo:
    def __init__(self, type_row: DiagnosisType | None):
        self._type = type_row

    async def get_type_by_id(self, type_id: str) -> DiagnosisType | None:
        return self._type


async def test_an_available_type_is_accepted():
    await _assert_available_type(_Repo(_type()), "t_career")


async def test_an_unknown_type_is_a_404():
    with pytest.raises(HTTPException) as raised:
        await _assert_available_type(_Repo(None), "t_missing")

    assert raised.value.status_code == 404
    assert "Diagnosis type" in raised.value.detail


async def test_a_deactivated_type_is_refused():
    with pytest.raises(HTTPException) as raised:
        await _assert_available_type(_Repo(_type(is_active=False)), "t_career")

    assert raised.value.status_code == 409


async def test_a_dated_retirement_is_refused_even_while_still_flagged_active():
    """Both conditions gate the read, so both have to gate the move."""
    from datetime import UTC, datetime

    retired = _type(is_active=True, effective_until=datetime.now(UTC))

    with pytest.raises(HTTPException) as raised:
        await _assert_available_type(_Repo(retired), "t_career")

    assert raised.value.status_code == 409
