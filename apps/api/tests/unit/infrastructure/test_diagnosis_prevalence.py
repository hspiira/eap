"""Diagnosis prevalence shaping and disclosure suppression.

Grouped at type level rather than by leaf: 52 leaves against the seeded
taxonomy would put most cells under the floor and say nothing.
"""

from app.infrastructure.services.report_query_runner import prevalence_payload

ROWS = [
    ("WORK_STRESS_ANXIETY", "Work Stress / Anxiety", 40),
    ("LOSS_GRIEF", "Loss & Grief", 12),
    ("GBV", "GBV (Gender-Based Violence)", 2),
]


def test_no_rows_reports_no_data():
    out = prevalence_payload([], unclassified=0)
    assert out["status"] == "no_data"
    assert out["buckets"] == []


def test_rows_report_ok():
    assert prevalence_payload(ROWS, unclassified=0)["status"] == "ok"


def test_counts_at_or_above_the_floor_survive():
    buckets = prevalence_payload(ROWS, unclassified=0, floor=5)["buckets"]
    by_code = {b["code"]: b["count"] for b in buckets}
    assert by_code["WORK_STRESS_ANXIETY"] == 40
    assert by_code["LOSS_GRIEF"] == 12


def test_a_small_cell_is_suppressed_but_its_label_is_kept():
    buckets = prevalence_payload(ROWS, unclassified=0, floor=5)["buckets"]
    gbv = next(b for b in buckets if b["code"] == "GBV")
    assert gbv["count"] == "<5"
    assert gbv["label"] == "GBV (Gender-Based Violence)"


def test_the_total_counts_suppressed_cells():
    """Suppression hides a cell, it does not remove it from the total."""
    assert prevalence_payload(ROWS, unclassified=0, floor=5)["total"] == 54


def test_unclassified_sessions_are_reported_separately():
    out = prevalence_payload(ROWS, unclassified=31, floor=5)
    assert out["unclassified_sessions"] == 31
    assert out["total"] == 54


def test_a_small_unclassified_count_is_suppressed_too():
    assert prevalence_payload(ROWS, unclassified=3, floor=5)["unclassified_sessions"] == "<5"


def test_a_lower_floor_suppresses_less():
    buckets = prevalence_payload(ROWS, unclassified=0, floor=2)["buckets"]
    assert next(b for b in buckets if b["code"] == "GBV")["count"] == 2
