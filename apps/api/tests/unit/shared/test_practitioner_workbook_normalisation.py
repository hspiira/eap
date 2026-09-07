"""Role normalisation: explicit table, no fuzzing, and drift against the file."""

import os
from collections import Counter
from pathlib import Path

import pytest

from app.shared.utils.practitioner_workbook import (
    CONSULTANTS_SHEET,
    PARTNER_SHEET,
    parse_practitioner_workbook,
)
from app.shared.utils.practitioner_workbook_normalisation import (
    PROFESSION_COLUMN,
    SPECIALITY_COLUMN,
    Unmapped,
    map_profession,
    map_role,
    map_speciality,
    table_keys,
)

REFERENCE_ENV = "PRACTITIONERS_REFERENCE_XLSX"


class TestLookup:
    def test_spelling_variants_of_one_role_collapse(self):
        assert map_profession("Clinical Psychology") == "Clinical Psychologist"
        assert map_profession("Clincal Psychologist") == "Clinical Psychologist"
        assert map_profession("Counseling Psychologist") == "Counselling Psychologist"
        assert map_speciality("Counseling") == "Counselling"
        assert map_speciality("Counselling") == "Counselling"

    def test_lookup_strips_collapses_and_casefolds(self):
        assert map_profession("  clinical   PSYCHOLOGIST ") == "Clinical Psychologist"

    def test_an_unlisted_value_is_unmapped_never_defaulted(self):
        result = map_profession("Clinical Psychologist (Trauma)")
        assert result == Unmapped(column=PROFESSION_COLUMN, value="Clinical Psychologist (Trauma)")

    def test_blank_stays_blank(self):
        assert map_profession(None) is None
        assert map_profession("   ") is None
        assert map_speciality(None) is None

    def test_map_role_dispatches_by_column(self):
        assert map_role(PROFESSION_COLUMN, "Psychiatrist") == "Psychiatrist"
        assert map_role(SPECIALITY_COLUMN, "Financial Coach") == "Financial Coach"
        with pytest.raises(ValueError):
            map_role("NO SUCH COLUMN", "x")

    def test_topics_are_not_promoted_to_roles(self):
        assert isinstance(map_speciality("Depression/Trauma"), Unmapped)
        assert isinstance(map_speciality("Minet Media"), Unmapped)


@pytest.fixture(scope="module")
def distinct():
    rows = parse_practitioner_workbook(Path(os.environ[REFERENCE_ENV]).read_bytes())
    professions = Counter(
        " ".join(r.raw_profession.split()).casefold()
        for r in rows
        if r.sheet_name == PARTNER_SHEET.name and r.raw_profession
    )
    specialities = Counter(
        " ".join(r.raw_profession.split()).casefold()
        for r in rows
        if r.sheet_name == CONSULTANTS_SHEET.name and r.raw_profession
    )
    return professions, specialities


@pytest.mark.skipif(REFERENCE_ENV not in os.environ, reason=f"Set {REFERENCE_ENV}")
class TestDriftAgainstReferenceFile:
    """The tables were enumerated from the reference file; hold them to it."""

    def test_the_distinct_value_counts_hold(self, distinct):
        professions, specialities = distinct
        assert len(professions) == 57
        assert len(specialities) == 50

    def test_every_table_key_still_occurs_in_the_file(self, distinct):
        professions, specialities = distinct
        assert table_keys(PROFESSION_COLUMN) <= set(professions)
        assert table_keys(SPECIALITY_COLUMN) <= set(specialities)

    def test_mapped_row_coverage_is_stated_honestly(self, distinct):
        """21/57 profession and 7/50 speciality spellings map, no more."""
        professions, specialities = distinct
        assert len(table_keys(PROFESSION_COLUMN)) == 21
        assert len(table_keys(SPECIALITY_COLUMN)) == 7
        mapped_profession_rows = sum(
            count for key, count in professions.items() if key in table_keys(PROFESSION_COLUMN)
        )
        mapped_speciality_rows = sum(
            count for key, count in specialities.items() if key in table_keys(SPECIALITY_COLUMN)
        )
        assert mapped_profession_rows == 64
        assert mapped_speciality_rows == 13
