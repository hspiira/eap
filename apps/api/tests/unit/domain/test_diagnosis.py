"""Diagnosis taxonomy entity tests (Phase 2 #D-Tax)."""

from app.domain.entities.diagnosis import Diagnosis, DiagnosisType


def test_diagnosis_type_is_immutable():
    t = DiagnosisType(
        id="dt-1",
        code="MH",
        name="Mental Health",
        description=None,
        sort_order=0,
        is_active=True,
        version=1,
        effective_until=None,
    )
    try:
        t.name = "Other"  # type: ignore[misc]
    except Exception:
        return
    raise AssertionError("DiagnosisType should be frozen / immutable")


def test_diagnosis_carries_type_id():
    d = Diagnosis(
        id="dx-1",
        type_id="dt-1",
        code="DEP",
        name="Depression",
        description=None,
        sort_order=0,
        is_active=True,
        version=1,
        effective_until=None,
    )
    assert d.type_id == "dt-1"
    assert d.code == "DEP"
    assert d.is_active is True
