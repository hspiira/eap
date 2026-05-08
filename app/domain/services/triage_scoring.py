"""Triage instrument catalogue + scoring (Phase 3 #D-Triage / ADR-015).

Instrument definitions are immutable in-process constants. Scoring is a pure
function of (instrument, raw responses) → ``QuestionnaireResponse`` so the
result is reproducible from stored answers regardless of catalogue evolution.

Scoring rules (SAD §B.4 / §2.3.1):

* **JOSEPH7** — 7 Likert items 0..3; ``total ∈ [0, 21]``. Risk bands: 0-4 LOW,
  5-9 MODERATE, 10-14 HIGH, 15+ CRITICAL. Stage-of-Change derived from item 7
  (motivation) — the higher the score, the further along the change spectrum.
* **WOS5** — 5 Likert items 1..5; pre/post case captured separately. Reports
  carry both ``raw`` (5..25) and ``normalised_0_100`` so renewal packs can
  show pre→post deltas on a familiar scale. Risk band derives from raw total.
* **PHQ9** — 9 items 0..3; ``total ∈ [0, 27]``. Standard severity bands. Item 9
  asks about self-harm ideation: any non-zero answer raises the crisis flag
  irrespective of total severity (SAD §6.3 acceptance criterion).
"""

from __future__ import annotations

from app.domain.enums import (
    StageOfChange,
    TriageInstrumentCode,
    TriageRiskLevel,
)
from app.domain.value_objects.triage import (
    Questionnaire,
    QuestionnaireItem,
    QuestionnaireResponse,
)

JOSEPH7 = Questionnaire(
    code=TriageInstrumentCode.JOSEPH7,
    version="1",
    title="Joseph 7-variable counsellor-callback screen",
    items=(
        QuestionnaireItem("q1", "Reported distress level", 0, 3),
        QuestionnaireItem("q2", "Sleep disruption", 0, 3),
        QuestionnaireItem("q3", "Concentration / cognitive load", 0, 3),
        QuestionnaireItem("q4", "Social withdrawal", 0, 3),
        QuestionnaireItem("q5", "Substance reliance", 0, 3),
        QuestionnaireItem("q6", "Functional impairment at work", 0, 3),
        QuestionnaireItem("q7", "Motivation to engage support", 0, 3),
    ),
)

WOS5 = Questionnaire(
    code=TriageInstrumentCode.WOS5,
    version="1",
    title="Work Outcome Scale (WOS-5)",
    items=(
        QuestionnaireItem("w1", "Productivity at work in the past two weeks", 1, 5),
        QuestionnaireItem("w2", "Workplace relationships in the past two weeks", 1, 5),
        QuestionnaireItem("w3", "Absenteeism / presenteeism", 1, 5),
        QuestionnaireItem("w4", "Job satisfaction", 1, 5),
        QuestionnaireItem("w5", "Overall functioning at work", 1, 5),
    ),
)

PHQ9 = Questionnaire(
    code=TriageInstrumentCode.PHQ9,
    version="1",
    title="Patient Health Questionnaire (PHQ-9)",
    items=(
        QuestionnaireItem("item1", "Little interest or pleasure in doing things", 0, 3),
        QuestionnaireItem("item2", "Feeling down, depressed, or hopeless", 0, 3),
        QuestionnaireItem("item3", "Trouble falling or staying asleep", 0, 3),
        QuestionnaireItem("item4", "Feeling tired or having little energy", 0, 3),
        QuestionnaireItem("item5", "Poor appetite or overeating", 0, 3),
        QuestionnaireItem("item6", "Feeling bad about yourself", 0, 3),
        QuestionnaireItem("item7", "Trouble concentrating", 0, 3),
        QuestionnaireItem("item8", "Moving or speaking slowly / restlessness", 0, 3),
        QuestionnaireItem("item9", "Thoughts that you would be better off dead or of self-harm", 0, 3),
    ),
)


CATALOGUE: dict[TriageInstrumentCode, Questionnaire] = {
    TriageInstrumentCode.JOSEPH7: JOSEPH7,
    TriageInstrumentCode.WOS5: WOS5,
    TriageInstrumentCode.PHQ9: PHQ9,
}


def get_instrument(code: TriageInstrumentCode) -> Questionnaire:
    """Look up the current version of an instrument by code."""
    try:
        return CATALOGUE[code]
    except KeyError as exc:
        label = code.value if isinstance(code, TriageInstrumentCode) else repr(code)
        raise KeyError(f"Unknown triage instrument: {label}") from exc


def _classify_joseph_stage(motivation_score: int) -> StageOfChange:
    """Map Joseph item-7 motivation (0..3) to Prochaska stage."""
    if motivation_score <= 0:
        return StageOfChange.PRECONTEMPLATION
    if motivation_score == 1:
        return StageOfChange.CONTEMPLATION
    if motivation_score == 2:
        return StageOfChange.PREPARATION
    return StageOfChange.ACTION


def _score_joseph7(responses: dict[str, int]) -> QuestionnaireResponse:
    total = sum(responses.values())
    if total >= 15:
        risk = TriageRiskLevel.CRITICAL
    elif total >= 10:
        risk = TriageRiskLevel.HIGH
    elif total >= 5:
        risk = TriageRiskLevel.MODERATE
    else:
        risk = TriageRiskLevel.LOW
    stage = _classify_joseph_stage(responses["q7"])
    crisis = risk == TriageRiskLevel.CRITICAL
    return QuestionnaireResponse(
        instrument_code=TriageInstrumentCode.JOSEPH7,
        instrument_version=JOSEPH7.version,
        responses=dict(responses),
        scores={"total": total, "max": 21},
        risk_level=risk,
        crisis_flag=crisis,
        crisis_reason=("JOSEPH7 total ≥ 15 (critical band)" if crisis else None),
        derived={"stage_of_change": stage.value},
    )


def _score_wos5(responses: dict[str, int]) -> QuestionnaireResponse:
    raw = sum(responses.values())
    # 5..25 → 0..100
    normalised = ((raw - 5) / 20) * 100
    if raw <= 10:
        risk = TriageRiskLevel.HIGH
    elif raw <= 17:
        risk = TriageRiskLevel.MODERATE
    else:
        risk = TriageRiskLevel.LOW
    return QuestionnaireResponse(
        instrument_code=TriageInstrumentCode.WOS5,
        instrument_version=WOS5.version,
        responses=dict(responses),
        scores={"raw": raw, "max": 25, "normalised_0_100": round(normalised, 2)},
        risk_level=risk,
        crisis_flag=False,
        crisis_reason=None,
        derived={},
    )


def _score_phq9(responses: dict[str, int]) -> QuestionnaireResponse:
    total = sum(responses.values())
    if total >= 20:
        risk = TriageRiskLevel.CRITICAL
    elif total >= 15:
        risk = TriageRiskLevel.HIGH
    elif total >= 10:
        risk = TriageRiskLevel.MODERATE
    else:
        risk = TriageRiskLevel.LOW
    item9 = responses["item9"]
    crisis = item9 > 0 or risk == TriageRiskLevel.CRITICAL
    if item9 > 0:
        reason = "PHQ-9 item 9 > 0 (self-harm ideation)"
    elif crisis:
        reason = "PHQ-9 total ≥ 20 (severe depression)"
    else:
        reason = None
    return QuestionnaireResponse(
        instrument_code=TriageInstrumentCode.PHQ9,
        instrument_version=PHQ9.version,
        responses=dict(responses),
        scores={"total": total, "max": 27, "item9": item9},
        risk_level=risk,
        crisis_flag=crisis,
        crisis_reason=reason,
        derived={},
    )


_SCORERS = {
    TriageInstrumentCode.JOSEPH7: _score_joseph7,
    TriageInstrumentCode.WOS5: _score_wos5,
    TriageInstrumentCode.PHQ9: _score_phq9,
}


def score_triage(
    code: TriageInstrumentCode, responses: dict[str, int]
) -> QuestionnaireResponse:
    """Validate and score raw triage answers against the current catalogue.

    Raises ``ValueError`` for unknown instruments, missing/extra item codes,
    non-integer answers, or out-of-range Likert values.
    """
    instrument = get_instrument(code)
    instrument.validate_responses(responses)
    return _SCORERS[code](responses)
