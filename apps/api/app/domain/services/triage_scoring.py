"""Triage instrument catalogue + scoring (Phase 3 #D-Triage / ADR-015).

Instrument definitions are immutable in-process constants. Scoring is a pure
function of (instrument, raw responses) → ``QuestionnaireResponse`` so the
result is reproducible from stored answers regardless of catalogue evolution.

Scoring rules (SAD §B.4 / §2.3.1):

* **JOSEPH7**: 7 Likert items 0..3; ``total ∈ [0, 21]``. Risk bands: 0-4 LOW,
  5-9 MODERATE, 10-14 HIGH, 15+ CRITICAL. Stage-of-Change derived from item 7
  (motivation); the higher the score, the further along the change spectrum.
* **WOS5**: 5 Likert items 1..5; pre/post case captured separately. Reports
  carry both ``raw`` (5..25) and ``normalised_0_100`` so renewal packs can
  show pre→post deltas on a familiar scale. Risk band derives from raw total.
* **PHQ9**: 9 items 0..3; ``total ∈ [0, 27]``. Standard severity bands. Item 9
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
        QuestionnaireItem(
            "item9", "Thoughts that you would be better off dead or of self-harm", 0, 3
        ),
    ),
)


GAD7 = Questionnaire(
    code=TriageInstrumentCode.GAD7,
    version="1",
    title="Generalized Anxiety Disorder (GAD-7)",
    items=tuple(QuestionnaireItem(f"g{i}", f"Item {i}", 0, 3) for i in range(1, 8)),
)

CSSRS = Questionnaire(
    code=TriageInstrumentCode.CSSRS,
    version="1-brief",
    title="Columbia Suicide Severity Rating Scale (brief)",
    items=(
        QuestionnaireItem("c1", "Wish to be dead", 0, 1),
        QuestionnaireItem("c2", "Non-specific active suicidal thoughts", 0, 1),
        QuestionnaireItem("c3", "Active ideation with method (without plan)", 0, 1),
        QuestionnaireItem("c4", "Active ideation with intent (without specific plan)", 0, 1),
        QuestionnaireItem("c5", "Active ideation with specific plan and intent", 0, 1),
        QuestionnaireItem("c6", "Suicide behaviour in lifetime", 0, 1),
        QuestionnaireItem(
            "c6_recent",
            "Suicide behaviour within past 3 months",
            0,
            1,
        ),
    ),
)

AUDIT_C = Questionnaire(
    code=TriageInstrumentCode.AUDIT_C,
    version="1",
    title="AUDIT-C alcohol-use screen",
    items=tuple(QuestionnaireItem(f"a{i}", f"Item {i}", 0, 4) for i in range(1, 4)),
)

DAST10 = Questionnaire(
    code=TriageInstrumentCode.DAST10,
    version="1",
    title="Drug Abuse Screening Test (10-item)",
    items=tuple(QuestionnaireItem(f"d{i}", f"Item {i}", 0, 1) for i in range(1, 11)),
)

WHO5 = Questionnaire(
    code=TriageInstrumentCode.WHO5,
    version="1",
    title="WHO-5 Wellbeing Index",
    items=tuple(QuestionnaireItem(f"h{i}", f"Item {i}", 0, 5) for i in range(1, 6)),
)

K10 = Questionnaire(
    code=TriageInstrumentCode.K10,
    version="1",
    title="Kessler Psychological Distress Scale (K10)",
    items=tuple(QuestionnaireItem(f"k{i}", f"Item {i}", 1, 5) for i in range(1, 11)),
)

WSAS = Questionnaire(
    code=TriageInstrumentCode.WSAS,
    version="1",
    title="Work and Social Adjustment Scale",
    items=tuple(QuestionnaireItem(f"s{i}", f"Item {i}", 0, 8) for i in range(1, 6)),
)

DASS21 = Questionnaire(
    code=TriageInstrumentCode.DASS21,
    version="1",
    title="Depression, Anxiety, Stress Scale (21-item)",
    items=tuple(QuestionnaireItem(f"da{i}", f"Item {i}", 0, 3) for i in range(1, 22)),
)

PCL5 = Questionnaire(
    code=TriageInstrumentCode.PCL5,
    version="1",
    title="PTSD Checklist for DSM-5 (PCL-5)",
    items=tuple(QuestionnaireItem(f"p{i}", f"Item {i}", 0, 4) for i in range(1, 21)),
)


CATALOGUE: dict[TriageInstrumentCode, Questionnaire] = {
    TriageInstrumentCode.JOSEPH7: JOSEPH7,
    TriageInstrumentCode.WOS5: WOS5,
    TriageInstrumentCode.PHQ9: PHQ9,
    TriageInstrumentCode.GAD7: GAD7,
    TriageInstrumentCode.CSSRS: CSSRS,
    TriageInstrumentCode.AUDIT_C: AUDIT_C,
    TriageInstrumentCode.DAST10: DAST10,
    TriageInstrumentCode.WHO5: WHO5,
    TriageInstrumentCode.K10: K10,
    TriageInstrumentCode.WSAS: WSAS,
    TriageInstrumentCode.DASS21: DASS21,
    TriageInstrumentCode.PCL5: PCL5,
}


def get_instrument(code: TriageInstrumentCode) -> Questionnaire:
    """Look up the current version of an instrument by code."""
    try:
        return CATALOGUE[code]
    except KeyError as exc:
        raise KeyError(f"Unknown triage instrument: {code.value}") from exc


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


def _band_total(total: int, *, max_score: int, code: TriageInstrumentCode) -> TriageRiskLevel:
    """Standard four-band classifier scaling against the instrument's max."""
    if max_score <= 0:
        return TriageRiskLevel.LOW
    pct = total / max_score
    if pct >= 0.75:
        return TriageRiskLevel.CRITICAL
    if pct >= 0.5:
        return TriageRiskLevel.HIGH
    if pct >= 0.25:
        return TriageRiskLevel.MODERATE
    return TriageRiskLevel.LOW


def _score_gad7(responses: dict[str, int]) -> QuestionnaireResponse:
    total = sum(responses.values())
    if total >= 15:
        risk = TriageRiskLevel.HIGH
    elif total >= 10:
        risk = TriageRiskLevel.MODERATE
    elif total >= 5:
        risk = TriageRiskLevel.LOW
    else:
        risk = TriageRiskLevel.LOW
    return QuestionnaireResponse(
        instrument_code=TriageInstrumentCode.GAD7,
        instrument_version=GAD7.version,
        responses=dict(responses),
        scores={"total": total, "max": 21},
        risk_level=risk,
        crisis_flag=False,
        crisis_reason=None,
        derived={},
    )


def _score_cssrs(responses: dict[str, int]) -> QuestionnaireResponse:
    """C-SSRS brief: any non-zero answer to items 3-5 (active ideation with
    method/intent/plan) or items 6 (lifetime behaviour) flips CRITICAL +
    crisis. Items 1-2 alone are MODERATE; all zero is LOW."""
    high_risk_items = ("c3", "c4", "c5", "c6_recent")
    lifetime_behaviour = responses.get("c6", 0) > 0
    has_high = any(responses.get(k, 0) > 0 for k in high_risk_items)
    if has_high:
        risk = TriageRiskLevel.CRITICAL
        crisis = True
        reason = "C-SSRS active ideation with plan/intent or recent behaviour"
    elif lifetime_behaviour:
        risk = TriageRiskLevel.HIGH
        crisis = True
        reason = "C-SSRS lifetime suicide behaviour reported"
    elif responses.get("c1", 0) > 0 or responses.get("c2", 0) > 0:
        risk = TriageRiskLevel.MODERATE
        crisis = False
        reason = None
    else:
        risk = TriageRiskLevel.LOW
        crisis = False
        reason = None
    return QuestionnaireResponse(
        instrument_code=TriageInstrumentCode.CSSRS,
        instrument_version=CSSRS.version,
        responses=dict(responses),
        scores={"any_high_risk": has_high, "lifetime_behaviour": lifetime_behaviour},
        risk_level=risk,
        crisis_flag=crisis,
        crisis_reason=reason,
        derived={},
    )


def _score_audit_c(responses: dict[str, int]) -> QuestionnaireResponse:
    total = sum(responses.values())
    if total >= 8:
        risk = TriageRiskLevel.HIGH
    elif total >= 4:
        risk = TriageRiskLevel.MODERATE
    else:
        risk = TriageRiskLevel.LOW
    return QuestionnaireResponse(
        instrument_code=TriageInstrumentCode.AUDIT_C,
        instrument_version=AUDIT_C.version,
        responses=dict(responses),
        scores={"total": total, "max": 12},
        risk_level=risk,
        crisis_flag=False,
        crisis_reason=None,
        derived={},
    )


def _score_dast10(responses: dict[str, int]) -> QuestionnaireResponse:
    total = sum(responses.values())
    if total >= 9:
        risk = TriageRiskLevel.HIGH
    elif total >= 6:
        risk = TriageRiskLevel.MODERATE
    elif total >= 3:
        risk = TriageRiskLevel.LOW
    else:
        risk = TriageRiskLevel.LOW
    return QuestionnaireResponse(
        instrument_code=TriageInstrumentCode.DAST10,
        instrument_version=DAST10.version,
        responses=dict(responses),
        scores={"total": total, "max": 10},
        risk_level=risk,
        crisis_flag=False,
        crisis_reason=None,
        derived={},
    )


def _score_who5(responses: dict[str, int]) -> QuestionnaireResponse:
    raw = sum(responses.values())
    normalised = raw * 4
    if normalised <= 28:
        risk = TriageRiskLevel.HIGH
    elif normalised <= 50:
        risk = TriageRiskLevel.MODERATE
    else:
        risk = TriageRiskLevel.LOW
    return QuestionnaireResponse(
        instrument_code=TriageInstrumentCode.WHO5,
        instrument_version=WHO5.version,
        responses=dict(responses),
        scores={"raw": raw, "normalised_0_100": normalised, "max": 25},
        risk_level=risk,
        crisis_flag=False,
        crisis_reason=None,
        derived={},
    )


def _score_k10(responses: dict[str, int]) -> QuestionnaireResponse:
    total = sum(responses.values())
    if total >= 30:
        risk = TriageRiskLevel.CRITICAL
    elif total >= 25:
        risk = TriageRiskLevel.HIGH
    elif total >= 20:
        risk = TriageRiskLevel.MODERATE
    else:
        risk = TriageRiskLevel.LOW
    return QuestionnaireResponse(
        instrument_code=TriageInstrumentCode.K10,
        instrument_version=K10.version,
        responses=dict(responses),
        scores={"total": total, "max": 50},
        risk_level=risk,
        crisis_flag=False,
        crisis_reason=None,
        derived={},
    )


def _score_wsas(responses: dict[str, int]) -> QuestionnaireResponse:
    total = sum(responses.values())
    if total >= 21:
        risk = TriageRiskLevel.HIGH
    elif total >= 10:
        risk = TriageRiskLevel.MODERATE
    else:
        risk = TriageRiskLevel.LOW
    return QuestionnaireResponse(
        instrument_code=TriageInstrumentCode.WSAS,
        instrument_version=WSAS.version,
        responses=dict(responses),
        scores={"total": total, "max": 40},
        risk_level=risk,
        crisis_flag=False,
        crisis_reason=None,
        derived={},
    )


def _score_dass21(responses: dict[str, int]) -> QuestionnaireResponse:
    total = sum(responses.values())
    risk = _band_total(total, max_score=63, code=TriageInstrumentCode.DASS21)
    return QuestionnaireResponse(
        instrument_code=TriageInstrumentCode.DASS21,
        instrument_version=DASS21.version,
        responses=dict(responses),
        scores={"total": total, "max": 63},
        risk_level=risk,
        crisis_flag=False,
        crisis_reason=None,
        derived={},
    )


def _score_pcl5(responses: dict[str, int]) -> QuestionnaireResponse:
    total = sum(responses.values())
    if total >= 33:
        risk = TriageRiskLevel.HIGH
    elif total >= 21:
        risk = TriageRiskLevel.MODERATE
    else:
        risk = TriageRiskLevel.LOW
    return QuestionnaireResponse(
        instrument_code=TriageInstrumentCode.PCL5,
        instrument_version=PCL5.version,
        responses=dict(responses),
        scores={"total": total, "max": 80},
        risk_level=risk,
        crisis_flag=False,
        crisis_reason=None,
        derived={},
    )


_SCORERS = {
    TriageInstrumentCode.JOSEPH7: _score_joseph7,
    TriageInstrumentCode.WOS5: _score_wos5,
    TriageInstrumentCode.PHQ9: _score_phq9,
    TriageInstrumentCode.GAD7: _score_gad7,
    TriageInstrumentCode.CSSRS: _score_cssrs,
    TriageInstrumentCode.AUDIT_C: _score_audit_c,
    TriageInstrumentCode.DAST10: _score_dast10,
    TriageInstrumentCode.WHO5: _score_who5,
    TriageInstrumentCode.K10: _score_k10,
    TriageInstrumentCode.WSAS: _score_wsas,
    TriageInstrumentCode.DASS21: _score_dass21,
    TriageInstrumentCode.PCL5: _score_pcl5,
}


def score_triage(code: TriageInstrumentCode, responses: dict[str, int]) -> QuestionnaireResponse:
    """Validate and score raw triage answers against the current catalogue.

    Raises ``ValueError`` for unknown instruments, missing/extra item codes,
    non-integer answers, or out-of-range Likert values.
    """
    instrument = get_instrument(code)
    instrument.validate_responses(responses)
    return _SCORERS[code](responses)
