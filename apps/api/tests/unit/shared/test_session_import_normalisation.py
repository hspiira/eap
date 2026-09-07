"""Normalisation tables for the session import, measured against the extract.

Every mapped spelling below appears in the reference extract
(sha256 0e8fa212455ea42bba48574eb46c639ade1238bc9fa7382bfc7eee1951774e44,
7,470 populated rows). The drift test at the bottom reruns the whole file
through every mapper and pins the per-column counts, so a future extract
that adds a spelling fails visibly instead of importing silently.
"""

import csv
import os
from collections import Counter
from pathlib import Path

import pytest

from app.domain.enums import (
    ClientType,
    MemberGender,
    SessionAttendance,
    SessionCategory,
    SessionClinicalStatus,
    SessionStatus,
    SessionType,
)
from app.shared.utils.session_import_normalisation import (
    StatusMapping,
    Unmapped,
    classify_gender,
    map_category,
    map_classification,
    map_client_type,
    map_diagnosis,
    map_diagnosis_type,
    map_session_type,
    map_status,
)


class TestSessionType:
    @pytest.mark.parametrize("raw", ["Physical", "physical", "PhysicaL"])
    def test_physical_spellings(self, raw):
        assert map_session_type(raw) is SessionType.PHYSICAL

    @pytest.mark.parametrize("raw", ["Online", "online"])
    def test_online_spellings(self, raw):
        assert map_session_type(raw) is SessionType.ONLINE

    def test_unknown_value_is_unmapped(self):
        assert map_session_type("Hybrid") == Unmapped(column="SESSION TYPE", value="Hybrid")

    @pytest.mark.parametrize("raw", [None, "", "  "])
    def test_blank_stays_blank(self, raw):
        assert map_session_type(raw) is None


class TestCategory:
    @pytest.mark.parametrize(
        "raw",
        [
            "Individual",
            "individual",
            "Individual Conselling",
            "Individual counseling",
            "Indididual",
            "individuual",
        ],
    )
    def test_individual_spellings(self, raw):
        assert map_category(raw) is SessionCategory.INDIVIDUAL

    @pytest.mark.parametrize(
        "raw",
        [
            "Group",
            "GROUP",
            "Group session",
            "Group  Conselling",
            "Onsite Group",
            "Health talk",
            "Group Presentation",
        ],
    )
    def test_group_spellings(self, raw):
        assert map_category(raw) is SessionCategory.GROUP

    @pytest.mark.parametrize("raw", ["Family", "Family Conselling"])
    def test_family_spellings(self, raw):
        assert map_category(raw) is SessionCategory.FAMILY

    @pytest.mark.parametrize("raw", ["Couple", "couple conselling", "Couples counselling"])
    def test_couples_spellings(self, raw):
        assert map_category(raw) is SessionCategory.COUPLES

    @pytest.mark.parametrize(
        "raw",
        [
            "Depression",
            "Relationship",
            "Marriage",
            "10:00AM",
            "online",
            "hosp visit/Dr,s conference",
            "Many",
        ],
    )
    def test_topic_and_bleed_values_stay_unmapped(self, raw):
        assert map_category(raw) == Unmapped(column="CATEGORY", value=raw)

    def test_blank_stays_blank(self):
        assert map_category("") is None


class TestClientType:
    def test_both_values(self):
        assert map_client_type("New") is ClientType.NEW
        assert map_client_type("Repeat") is ClientType.REPEAT

    def test_unknown_value_is_unmapped(self):
        assert map_client_type("Returning") == Unmapped(column="CLIENT TYPE", value="Returning")

    def test_blank_stays_blank(self):
        assert map_client_type(None) is None


class TestStatus:
    @pytest.mark.parametrize(
        ("raw", "expected"),
        [
            ("Ongoing", SessionClinicalStatus.TO_BE_CONTINUED),
            ("Completed", SessionClinicalStatus.COMPLETED),
            ("Referred", SessionClinicalStatus.REFERRED),
            ("Terminated", SessionClinicalStatus.TERMINATED),
        ],
    )
    def test_clinical_statuses_carry_no_scheduling_side(self, raw, expected):
        assert map_status(raw) == StatusMapping(clinical_status=expected, session_status=None)

    def test_no_show_is_a_scheduling_status_not_a_clinical_outcome(self):
        assert map_status("No Show") == StatusMapping(
            clinical_status=None, session_status=SessionStatus.NO_SHOW
        )

    def test_blank_gets_no_default(self):
        assert map_status("") is None
        assert map_status(None) is None

    def test_unknown_value_is_unmapped(self):
        assert map_status("Pending") == Unmapped(column="STATUS (CLEAN)", value="Pending")


class TestGender:
    @pytest.mark.parametrize("raw", ["Female", "female", "FEMALE"])
    def test_female_spellings(self, raw):
        assert classify_gender(raw) is MemberGender.FEMALE

    @pytest.mark.parametrize("raw", ["Male", "male", "MALE"])
    def test_male_spellings(self, raw):
        assert classify_gender(raw) is MemberGender.MALE

    @pytest.mark.parametrize("raw", ["Group", "group"])
    def test_group_is_the_company_wide_signal_not_a_gender(self, raw):
        assert classify_gender(raw) is SessionAttendance.COMPANY_WIDE

    def test_unknown_value_is_unmapped(self):
        assert classify_gender("Other") == Unmapped(column="GENDER", value="Other")


class TestClinicianBlockedColumns:
    """The tables stay empty until a clinician supplies the controlled list."""

    @pytest.mark.parametrize(
        ("mapper", "column", "raw"),
        [
            (map_diagnosis_type, "DIAGNOSIS TYPE", "Family___Relationship"),
            (map_diagnosis, "DIAGNOSIS", "Family or Relationship conflict"),
            (map_classification, "CLASSIFICATION", "Family &  Relationship"),
        ],
    )
    def test_every_value_is_unmapped(self, mapper, column, raw):
        assert mapper(raw) == Unmapped(column=column, value=raw)

    @pytest.mark.parametrize("mapper", [map_diagnosis_type, map_diagnosis, map_classification])
    def test_blank_stays_blank(self, mapper):
        assert mapper("") is None


REFERENCE_CSV = Path(
    os.environ.get("SESSIONS_REFERENCE_CSV", Path.home() / "Downloads" / "sessions.csv")
)

EXPECTED = {
    "SESSION TYPE": {"mapped": 7470, "unmapped": 0, "blank": 0, "distinct_unmapped": 0},
    "CATEGORY": {"mapped": 7024, "unmapped": 49, "blank": 397, "distinct_unmapped": 25},
    "CLIENT TYPE": {"mapped": 7462, "unmapped": 0, "blank": 8, "distinct_unmapped": 0},
    "STATUS (CLEAN)": {"mapped": 6659, "unmapped": 0, "blank": 811, "distinct_unmapped": 0},
    "GENDER": {"mapped": 7470, "unmapped": 0, "blank": 0, "distinct_unmapped": 0},
    "DIAGNOSIS TYPE": {"mapped": 0, "unmapped": 7451, "blank": 19, "distinct_unmapped": 63},
    "DIAGNOSIS": {"mapped": 0, "unmapped": 6721, "blank": 749, "distinct_unmapped": 251},
    "CLASSIFICATION": {"mapped": 0, "unmapped": 7470, "blank": 0, "distinct_unmapped": 28},
}

MAPPERS = {
    "SESSION TYPE": map_session_type,
    "CATEGORY": map_category,
    "CLIENT TYPE": map_client_type,
    "STATUS (CLEAN)": map_status,
    "GENDER": classify_gender,
    "DIAGNOSIS TYPE": map_diagnosis_type,
    "DIAGNOSIS": map_diagnosis,
    "CLASSIFICATION": map_classification,
}


@pytest.fixture(scope="module")
def rows():
    with REFERENCE_CSV.open(encoding="utf-8-sig", newline="") as handle:
        return [
            row
            for row in csv.DictReader(handle)
            if any((value or "").strip() for value in row.values())
        ]


@pytest.mark.skipif(
    not REFERENCE_CSV.is_file(),
    reason=f"reference extract not present at {REFERENCE_CSV}; set SESSIONS_REFERENCE_CSV to run",
)
class TestReferenceExtractCounts:
    """Every distinct value in the extract maps or is reported Unmapped.

    The counts pin the reference extract of 7,470 populated rows. A future
    file that drifts changes a count here rather than importing silently.
    """

    def test_row_count(self, rows):
        assert len(rows) == 7470

    @pytest.mark.parametrize("column", sorted(EXPECTED))
    def test_per_column_outcome_counts(self, rows, column):
        tally = Counter()
        distinct_unmapped = set()
        for row in rows:
            outcome = MAPPERS[column](row.get(column))
            if outcome is None:
                tally["blank"] += 1
            elif isinstance(outcome, Unmapped):
                tally["unmapped"] += 1
                distinct_unmapped.add(outcome.value)
            else:
                tally["mapped"] += 1
        observed = dict(tally, distinct_unmapped=len(distinct_unmapped))
        for key in ("mapped", "unmapped", "blank"):
            observed.setdefault(key, 0)
        assert observed == EXPECTED[column]

    def test_status_splits_across_the_two_enums(self, rows):
        outcomes = Counter(map_status(row.get("STATUS (CLEAN)")) for row in rows)
        clinical = sum(
            count
            for outcome, count in outcomes.items()
            if isinstance(outcome, StatusMapping) and outcome.clinical_status is not None
        )
        assert clinical == 6658
        assert outcomes[StatusMapping(session_status=SessionStatus.NO_SHOW)] == 1
        assert outcomes[None] == 811

    def test_company_wide_signal_count(self, rows):
        outcomes = Counter(classify_gender(row.get("GENDER")) for row in rows)
        assert outcomes[SessionAttendance.COMPANY_WIDE] == 642
        assert outcomes[MemberGender.FEMALE] == 4820
        assert outcomes[MemberGender.MALE] == 2008
