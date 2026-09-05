"""The tenant overlay hides, relabels, and reorders without touching the taxonomy."""

from app.api.routes.diagnoses import _build_tree
from app.domain.entities.diagnosis import Diagnosis, DiagnosisType, TenantOverlay


def _type(id_: str, name: str, order: int = 0) -> DiagnosisType:
    return DiagnosisType(
        id=id_,
        code=id_.upper(),
        name=name,
        description=None,
        sort_order=order,
        is_active=True,
        version=1,
        effective_until=None,
    )


def _dx(id_: str, type_id: str, name: str, order: int = 0) -> Diagnosis:
    return Diagnosis(
        id=id_,
        type_id=type_id,
        code=id_.upper(),
        name=name,
        description=None,
        sort_order=order,
        is_active=True,
        version=1,
        effective_until=None,
    )


def _overlay(type_id, diagnosis_id=None, *, enabled=True, order=None, label=None):
    return TenantOverlay(
        tenant_id="t1",
        diagnosis_type_id=type_id,
        diagnosis_id=diagnosis_id,
        is_enabled=enabled,
        sort_order=order,
        local_label=label,
    )


TYPES = [_type("t_gbv", "GBV", 1), _type("t_work", "Work Stress", 2)]
DIAGNOSES = [_dx("d_dv", "t_gbv", "Domestic Violence"), _dx("d_burn", "t_work", "Burnout")]


def test_no_overlay_returns_the_taxonomy_unchanged():
    tree = _build_tree(TYPES, DIAGNOSES, {})
    assert [t.name for t in tree] == ["GBV", "Work Stress"]
    assert [d.name for t in tree for d in t.diagnoses] == ["Domestic Violence", "Burnout"]


def test_a_disabled_type_disappears_for_that_tenant():
    tree = _build_tree(TYPES, DIAGNOSES, {("t_gbv", None): _overlay("t_gbv", enabled=False)})
    assert [t.name for t in tree] == ["Work Stress"]


def test_a_disabled_diagnosis_disappears_but_its_type_stays():
    overlay = {("t_gbv", "d_dv"): _overlay("t_gbv", "d_dv", enabled=False)}
    tree = _build_tree(TYPES, DIAGNOSES, overlay)
    gbv = next(t for t in tree if t.code == "T_GBV")
    assert gbv.diagnoses == []


def test_local_label_replaces_the_display_name_but_not_the_code():
    overlay = {("t_gbv", None): _overlay("t_gbv", label="Relationship Abuse")}
    gbv = next(t for t in _build_tree(TYPES, DIAGNOSES, overlay) if t.code == "T_GBV")
    assert gbv.name == "Relationship Abuse"
    assert gbv.code == "T_GBV"
    assert gbv.id == "t_gbv"


def test_sort_order_reorders_types():
    overlay = {("t_work", None): _overlay("t_work", order=0)}
    tree = _build_tree(TYPES, DIAGNOSES, overlay)
    assert [t.name for t in tree] == ["Work Stress", "GBV"]


def test_disabling_a_row_does_not_silently_reorder_it():
    """sort_order NULL means inherit; only an explicit value reorders."""
    overlay = {("t_work", None): _overlay("t_work", enabled=True)}
    tree = _build_tree(TYPES, DIAGNOSES, overlay)
    assert [t.name for t in tree] == ["GBV", "Work Stress"]


def test_zero_is_a_real_position_not_a_missing_value():
    overlay = {("t_work", None): _overlay("t_work", order=0)}
    tree = _build_tree(TYPES, DIAGNOSES, overlay)
    assert [t.name for t in tree] == ["Work Stress", "GBV"]


def test_overlay_does_not_mutate_the_shared_rows():
    _build_tree(TYPES, DIAGNOSES, {("t_gbv", None): _overlay("t_gbv", label="Renamed")})
    assert TYPES[0].name == "GBV"
