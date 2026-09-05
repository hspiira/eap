"""Legacy diagnosis strings resolve through aliases, or the row is rejected.

The reference extract holds 53 spellings for 29 concepts. Bucketing an
unrecognised value into Others would hide a missing alias behind a plausible
number, so an unmapped value fails the row instead.
"""

from app.application.services.historical_import import (
    AcceptedRow,
    CanonicalMappings,
    HistoricalSessionRow,
    ImportClassification,
    RejectedRow,
    validate_row,
)
from app.domain.enums import SessionStatus


def _mappings(**overrides) -> CanonicalMappings:
    base = dict(
        client_codes={"ABSA": "client-absa"},
        service_codes={"COUNSEL": "svc-1"},
        provider_codes={"DR-A": "prov-1"},
        person_codes={"E1234": "person-1"},
        status_text={"COMPLETED": SessionStatus.COMPLETED},
        diagnosis_aliases={
            "work stress anxiety": ("dt_work_stress_anxiety", None),
            "burnout": ("dt_work_stress_anxiety", "dx_burnout"),
        },
    )
    base.update(overrides)
    return CanonicalMappings(**base)


def _row(**overrides) -> HistoricalSessionRow:
    base = dict(
        source_id="excel-1",
        client_code="ABSA",
        service_code="COUNSEL",
        provider_code="DR-A",
        person_code="E1234",
        status_text="COMPLETED",
        scheduled_at_text="2024-09-15T10:00:00",
    )
    base.update(overrides)
    return HistoricalSessionRow(**base)


def _validate(row):
    return validate_row(row, _mappings(), set())


class TestDiagnosisResolution:
    def test_a_row_without_a_diagnosis_is_accepted(self):
        result = _validate(_row())
        assert isinstance(result, AcceptedRow)
        assert result.diagnosis_type_id is None
        assert result.diagnosis_id is None

    def test_blank_and_whitespace_are_not_errors(self):
        for value in ("", "   ", None):
            result = _validate(_row(diagnosis_text=value))
            assert isinstance(result, AcceptedRow), value
            assert result.diagnosis_type_id is None

    def test_a_spelling_with_no_alias_is_rejected_even_when_it_reads_familiar(self):
        """"Work Stress, Fatigue, Burnout" normalises to a key no alias covers."""
        result = _validate(_row(diagnosis_text="Work Stress, Fatigue, Burnout"))
        assert isinstance(result, RejectedRow)
        assert result.classification is ImportClassification.REJECTED_UNMAPPED_DIAGNOSIS

    def test_an_alias_resolves_to_its_type(self):
        result = _validate(_row(diagnosis_text="Work_Stress_Anxiety"))
        assert isinstance(result, AcceptedRow)
        assert result.diagnosis_type_id == "dt_work_stress_anxiety"
        assert result.diagnosis_id is None

    def test_an_alias_resolves_to_a_specific_diagnosis(self):
        result = _validate(_row(diagnosis_text="Burnout"))
        assert isinstance(result, AcceptedRow)
        assert result.diagnosis_id == "dx_burnout"

    def test_case_and_padding_variants_collapse_to_one_alias(self):
        for spelling in ("Burnout", "burnout", "  BURNOUT  ", "BurnOut"):
            result = _validate(_row(diagnosis_text=spelling))
            assert isinstance(result, AcceptedRow), spelling
            assert result.diagnosis_id == "dx_burnout", spelling

    def test_separators_collapse_to_one_key(self):
        """The shape that actually varies in the source: _ and & and doubled spaces."""
        for spelling in (
            "Work_Stress_Anxiety",
            "Work Stress Anxiety",
            "Work  Stress  Anxiety",
            "Work & Stress & Anxiety",
            "work-stress-anxiety",
        ):
            result = _validate(_row(diagnosis_text=spelling))
            assert isinstance(result, AcceptedRow), spelling
            assert result.diagnosis_type_id == "dt_work_stress_anxiety", spelling

    def test_a_separator_is_a_word_boundary_not_a_deletion(self):
        """`Burn_out` is not `Burnout`. Pinned so the behaviour is deliberate.

        Every underscore in the source extract separates words that are also
        separated by a space or an ampersand elsewhere, so joining them would
        be wrong more often than right.
        """
        assert isinstance(_validate(_row(diagnosis_text="Burn_out")), RejectedRow)

    def test_an_unmapped_value_is_rejected_not_bucketed(self):
        result = _validate(_row(diagnosis_text="Nurturing mental wellness in the workplace"))
        assert isinstance(result, RejectedRow)
        assert result.classification is ImportClassification.REJECTED_UNMAPPED_DIAGNOSIS
        assert "Nurturing mental wellness" in result.detail

    def test_the_original_string_is_kept_as_the_issue_topic(self):
        result = _validate(_row(diagnosis_text="Work_Stress_Anxiety"))
        assert result.issue_topic == "Work_Stress_Anxiety"
