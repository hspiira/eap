"""Tests for the extended triage instrument catalogue scorers."""

from app.domain.enums import TriageInstrumentCode, TriageRiskLevel
from app.domain.services.triage_scoring import CATALOGUE, score_triage


class TestCatalogueRegistration:
    def test_all_twelve_instruments_present(self):
        assert set(CATALOGUE.keys()) == set(TriageInstrumentCode)
        assert len(CATALOGUE) == 12


class TestGAD7:
    def test_low_band(self):
        responses = {f"g{i}": 0 for i in range(1, 8)}
        result = score_triage(TriageInstrumentCode.GAD7, responses)
        assert result.risk_level == TriageRiskLevel.LOW

    def test_high_band(self):
        responses = {f"g{i}": 3 for i in range(1, 8)}
        result = score_triage(TriageInstrumentCode.GAD7, responses)
        assert result.risk_level == TriageRiskLevel.HIGH
        assert result.scores["total"] == 21


class TestCSSRS:
    def test_active_with_plan_raises_crisis(self):
        responses = {
            "c1": 0,
            "c2": 0,
            "c3": 0,
            "c4": 0,
            "c5": 1,
            "c6": 0,
            "c6_recent": 0,
        }
        result = score_triage(TriageInstrumentCode.CSSRS, responses)
        assert result.risk_level == TriageRiskLevel.CRITICAL
        assert result.crisis_flag is True
        assert "plan" in (result.crisis_reason or "")

    def test_recent_behaviour_raises_crisis(self):
        responses = {
            "c1": 0,
            "c2": 0,
            "c3": 0,
            "c4": 0,
            "c5": 0,
            "c6": 1,
            "c6_recent": 1,
        }
        result = score_triage(TriageInstrumentCode.CSSRS, responses)
        assert result.crisis_flag is True
        assert result.risk_level == TriageRiskLevel.CRITICAL

    def test_lifetime_behaviour_only(self):
        responses = {
            "c1": 0,
            "c2": 0,
            "c3": 0,
            "c4": 0,
            "c5": 0,
            "c6": 1,
            "c6_recent": 0,
        }
        result = score_triage(TriageInstrumentCode.CSSRS, responses)
        assert result.risk_level == TriageRiskLevel.HIGH
        assert result.crisis_flag is True

    def test_passive_only(self):
        responses = {
            "c1": 1,
            "c2": 0,
            "c3": 0,
            "c4": 0,
            "c5": 0,
            "c6": 0,
            "c6_recent": 0,
        }
        result = score_triage(TriageInstrumentCode.CSSRS, responses)
        assert result.risk_level == TriageRiskLevel.MODERATE
        assert result.crisis_flag is False

    def test_all_zero(self):
        responses = {
            "c1": 0,
            "c2": 0,
            "c3": 0,
            "c4": 0,
            "c5": 0,
            "c6": 0,
            "c6_recent": 0,
        }
        result = score_triage(TriageInstrumentCode.CSSRS, responses)
        assert result.risk_level == TriageRiskLevel.LOW
        assert result.crisis_flag is False


class TestAUDITC:
    def test_high_band(self):
        responses = {"a1": 4, "a2": 4, "a3": 4}
        result = score_triage(TriageInstrumentCode.AUDIT_C, responses)
        assert result.risk_level == TriageRiskLevel.HIGH

    def test_moderate_band(self):
        responses = {"a1": 2, "a2": 1, "a3": 1}
        result = score_triage(TriageInstrumentCode.AUDIT_C, responses)
        assert result.risk_level == TriageRiskLevel.MODERATE


class TestWHO5:
    def test_low_wellbeing_high_risk(self):
        responses = {f"h{i}": 0 for i in range(1, 6)}
        result = score_triage(TriageInstrumentCode.WHO5, responses)
        assert result.risk_level == TriageRiskLevel.HIGH
        assert result.scores["normalised_0_100"] == 0

    def test_full_wellbeing_low_risk(self):
        responses = {f"h{i}": 5 for i in range(1, 6)}
        result = score_triage(TriageInstrumentCode.WHO5, responses)
        assert result.risk_level == TriageRiskLevel.LOW
        assert result.scores["normalised_0_100"] == 100


class TestK10:
    def test_critical_band(self):
        responses = {f"k{i}": 5 for i in range(1, 11)}
        result = score_triage(TriageInstrumentCode.K10, responses)
        assert result.risk_level == TriageRiskLevel.CRITICAL

    def test_low_band(self):
        responses = {f"k{i}": 1 for i in range(1, 11)}
        result = score_triage(TriageInstrumentCode.K10, responses)
        assert result.risk_level == TriageRiskLevel.LOW


class TestWSAS:
    def test_high_band(self):
        responses = {f"s{i}": 8 for i in range(1, 6)}
        result = score_triage(TriageInstrumentCode.WSAS, responses)
        assert result.risk_level == TriageRiskLevel.HIGH


class TestDASS21:
    def test_critical_band(self):
        responses = {f"da{i}": 3 for i in range(1, 22)}
        result = score_triage(TriageInstrumentCode.DASS21, responses)
        assert result.risk_level == TriageRiskLevel.CRITICAL


class TestDAST10:
    def test_high_band(self):
        responses = {f"d{i}": 1 for i in range(1, 11)}
        result = score_triage(TriageInstrumentCode.DAST10, responses)
        assert result.risk_level == TriageRiskLevel.HIGH

    def test_low_band(self):
        responses = {f"d{i}": 0 for i in range(1, 11)}
        result = score_triage(TriageInstrumentCode.DAST10, responses)
        assert result.risk_level == TriageRiskLevel.LOW


class TestPCL5:
    def test_high_band(self):
        responses = {f"p{i}": 4 for i in range(1, 21)}
        result = score_triage(TriageInstrumentCode.PCL5, responses)
        assert result.risk_level == TriageRiskLevel.HIGH
