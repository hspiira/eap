"""Triage instrument scoring tests (Phase 3 #D-Triage / ADR-015)."""

import pytest

from app.domain.enums import (
    StageOfChange,
    TriageInstrumentCode,
    TriageRiskLevel,
)
from app.domain.services.triage_scoring import (
    CATALOGUE,
    JOSEPH7,
    PHQ9,
    WOS5,
    get_instrument,
    score_triage,
)
from app.domain.value_objects.triage import (
    Questionnaire,
    QuestionnaireItem,
    QuestionnaireResponse,
)

# ---------- Catalogue ----------


class TestCatalogue:
    def test_v1_instruments_registered(self):
        for code in {
            TriageInstrumentCode.JOSEPH7,
            TriageInstrumentCode.WOS5,
            TriageInstrumentCode.PHQ9,
        }:
            assert code in CATALOGUE

    def test_get_instrument_returns_definition(self):
        q = get_instrument(TriageInstrumentCode.JOSEPH7)
        assert q is JOSEPH7
        assert len(q.items) == 7

    def test_each_instrument_has_unique_item_codes(self):
        for q in CATALOGUE.values():
            codes = [it.code for it in q.items]
            assert len(codes) == len(set(codes)), q.code


# ---------- Questionnaire VO invariants ----------


class TestQuestionnaireInvariants:
    def test_rejects_empty_items(self):
        with pytest.raises(ValueError):
            Questionnaire(
                code=TriageInstrumentCode.WOS5,
                version="1",
                title="x",
                items=(),
            )

    def test_rejects_duplicate_item_codes(self):
        item = QuestionnaireItem("a", "x", 0, 3)
        with pytest.raises(ValueError):
            Questionnaire(
                code=TriageInstrumentCode.WOS5,
                version="1",
                title="x",
                items=(item, item),
            )

    def test_item_rejects_inverted_range(self):
        with pytest.raises(ValueError):
            QuestionnaireItem("a", "x", 5, 1)

    def test_validate_responses_missing(self):
        with pytest.raises(ValueError, match="missing"):
            JOSEPH7.validate_responses({"q1": 0})

    def test_validate_responses_unknown(self):
        responses = {it.code: 1 for it in JOSEPH7.items}
        responses["bogus"] = 1
        with pytest.raises(ValueError, match="unknown"):
            JOSEPH7.validate_responses(responses)

    def test_validate_responses_out_of_range(self):
        responses = {it.code: 1 for it in JOSEPH7.items}
        responses["q1"] = 99
        with pytest.raises(ValueError, match="outside"):
            JOSEPH7.validate_responses(responses)


# ---------- Joseph 7 ----------


def _joseph(**overrides: int) -> dict[str, int]:
    base = {f"q{i}": 0 for i in range(1, 8)}
    base.update(overrides)
    return base


class TestJoseph7:
    def test_low_band(self):
        r = score_triage(TriageInstrumentCode.JOSEPH7, _joseph(q1=1, q2=1, q3=1))
        assert r.risk_level == TriageRiskLevel.LOW
        assert r.scores["total"] == 3
        assert r.crisis_flag is False

    def test_moderate_band(self):
        r = score_triage(TriageInstrumentCode.JOSEPH7, _joseph(q1=2, q2=2, q3=2, q4=1))
        assert r.risk_level == TriageRiskLevel.MODERATE
        assert r.scores["total"] == 7

    def test_high_band(self):
        r = score_triage(
            TriageInstrumentCode.JOSEPH7,
            _joseph(q1=3, q2=3, q3=3, q4=2, q5=0),
        )
        assert r.risk_level == TriageRiskLevel.HIGH

    def test_critical_band_raises_crisis_flag(self):
        r = score_triage(
            TriageInstrumentCode.JOSEPH7,
            _joseph(q1=3, q2=3, q3=3, q4=3, q5=3, q6=0, q7=0),
        )
        assert r.scores["total"] == 15
        assert r.risk_level == TriageRiskLevel.CRITICAL
        assert r.crisis_flag is True
        assert r.crisis_reason and "JOSEPH7" in r.crisis_reason

    def test_stage_of_change_precontemplation(self):
        r = score_triage(TriageInstrumentCode.JOSEPH7, _joseph(q7=0))
        assert r.derived["stage_of_change"] == StageOfChange.PRECONTEMPLATION.value

    def test_stage_of_change_action(self):
        r = score_triage(TriageInstrumentCode.JOSEPH7, _joseph(q7=3))
        assert r.derived["stage_of_change"] == StageOfChange.ACTION.value


# ---------- WOS-5 ----------


def _wos(**overrides: int) -> dict[str, int]:
    base = {f"w{i}": 3 for i in range(1, 6)}
    base.update(overrides)
    return base


class TestWOS5:
    def test_floor_is_high_risk(self):
        r = score_triage(TriageInstrumentCode.WOS5, _wos(w1=1, w2=1, w3=1, w4=1, w5=1))
        assert r.scores["raw"] == 5
        assert r.scores["normalised_0_100"] == 0.0
        assert r.risk_level == TriageRiskLevel.HIGH
        assert r.crisis_flag is False

    def test_ceiling_is_low_risk(self):
        r = score_triage(TriageInstrumentCode.WOS5, _wos(w1=5, w2=5, w3=5, w4=5, w5=5))
        assert r.scores["raw"] == 25
        assert r.scores["normalised_0_100"] == 100.0
        assert r.risk_level == TriageRiskLevel.LOW

    def test_midpoint_is_moderate(self):
        r = score_triage(TriageInstrumentCode.WOS5, _wos())
        assert r.scores["raw"] == 15
        assert r.risk_level == TriageRiskLevel.MODERATE

    def test_normalisation_rounded(self):
        # raw=10 → (10-5)/20 * 100 = 25.0
        r = score_triage(TriageInstrumentCode.WOS5, _wos(w1=2, w2=2, w3=2, w4=2, w5=2))
        assert r.scores["normalised_0_100"] == 25.0


# ---------- PHQ-9 ----------


def _phq(**overrides: int) -> dict[str, int]:
    base = {f"item{i}": 0 for i in range(1, 10)}
    base.update(overrides)
    return base


class TestPHQ9:
    def test_low_band(self):
        r = score_triage(TriageInstrumentCode.PHQ9, _phq(item1=1, item2=1))
        assert r.risk_level == TriageRiskLevel.LOW
        assert r.crisis_flag is False

    def test_item9_nonzero_raises_crisis_even_at_low_total(self):
        r = score_triage(TriageInstrumentCode.PHQ9, _phq(item9=1))
        assert r.scores["total"] == 1
        assert r.crisis_flag is True
        assert r.crisis_reason and "item 9" in r.crisis_reason

    def test_critical_band_raises_crisis_via_total(self):
        responses = _phq(**{f"item{i}": 3 for i in range(1, 8)}, item8=0, item9=0)
        # Total = 7*3 = 21, risk = CRITICAL, crisis via total even with item9=0
        r = score_triage(TriageInstrumentCode.PHQ9, responses)
        assert r.scores["total"] == 21
        assert r.risk_level == TriageRiskLevel.CRITICAL
        assert r.crisis_flag is True
        assert r.crisis_reason and "severe depression" in r.crisis_reason


# ---------- Integration / negative paths ----------


class TestScoringNegatives:
    def test_validation_error_propagates(self):
        with pytest.raises(ValueError):
            score_triage(TriageInstrumentCode.JOSEPH7, {"q1": 0})

    def test_response_vo_requires_reason_when_crisis(self):
        with pytest.raises(ValueError, match="crisis_reason"):
            QuestionnaireResponse(
                instrument_code=TriageInstrumentCode.JOSEPH7,
                instrument_version="1",
                responses={},
                scores={},
                risk_level=TriageRiskLevel.CRITICAL,
                crisis_flag=True,
                crisis_reason=None,
            )

    def test_phq9_definition_has_nine_items(self):
        assert len(PHQ9.items) == 9

    def test_wos5_definition_has_five_items(self):
        assert len(WOS5.items) == 5
