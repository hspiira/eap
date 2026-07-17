"""Triage instrument value objects (Phase 3 #D-Triage / ADR-015 / ADR-008).

FHIR-aligned in shape: a ``Questionnaire`` is a versioned bundle of ``QuestionnaireItem``s,
and a ``QuestionnaireResponse`` records the answers a respondent supplied for one
administration. Instrument definitions are immutable in-process catalogue entries
(see ``app.domain.services.triage_scoring``) — only responses are persisted.
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, field
from typing import Any

from app.domain.enums import TriageInstrumentCode, TriageRiskLevel


@dataclass(frozen=True)
class QuestionnaireItem:
    """A single scoreable item on a triage instrument.

    ``code`` is the stable per-instrument question id (e.g. ``"q1"``, ``"item9"``);
    ``min_value`` / ``max_value`` define the inclusive Likert range.
    """

    code: str
    text: str
    min_value: int
    max_value: int

    def __post_init__(self) -> None:
        if not self.code:
            raise ValueError("QuestionnaireItem.code must be non-empty")
        if self.max_value < self.min_value:
            raise ValueError("QuestionnaireItem max_value must be >= min_value")

    def is_in_range(self, value: int) -> bool:
        return self.min_value <= value <= self.max_value


@dataclass(frozen=True)
class Questionnaire:
    """Versioned triage instrument definition (FHIR Questionnaire shape).

    Immutability is intentional: a new ``version`` is published rather than mutating
    an existing instrument. Persisted ``QuestionnaireResponse``s carry the
    ``instrument_code`` + ``version`` they were administered against so historical
    answers remain interpretable when the catalogue evolves.
    """

    code: TriageInstrumentCode
    version: str
    title: str
    items: tuple[QuestionnaireItem, ...]

    def __post_init__(self) -> None:
        if not self.version:
            raise ValueError("Questionnaire.version must be non-empty")
        if not self.items:
            raise ValueError("Questionnaire requires at least one item")
        seen: set[str] = set()
        for item in self.items:
            if item.code in seen:
                raise ValueError(f"Duplicate item code: {item.code}")
            seen.add(item.code)

    def item(self, code: str) -> QuestionnaireItem:
        for it in self.items:
            if it.code == code:
                return it
        raise KeyError(f"Unknown item code for {self.code.value}: {code}")

    def validate_responses(self, responses: Mapping[str, object]) -> None:
        """Reject malformed responses: unknown keys, out-of-range values, missing items."""
        expected = {it.code for it in self.items}
        provided = set(responses.keys())
        missing = expected - provided
        if missing:
            raise ValueError(
                f"{self.code.value} v{self.version}: missing answers for " + f"{sorted(missing)}"
            )
        unknown = provided - expected
        if unknown:
            raise ValueError(f"{self.code.value} v{self.version}: unknown items {sorted(unknown)}")
        for code, value in responses.items():
            item = self.item(code)
            if not isinstance(value, int):
                raise ValueError(f"{code}: expected int, got {type(value).__name__}")
            if not item.is_in_range(value):
                raise ValueError(
                    f"{code}: value {value} outside [{item.min_value}, {item.max_value}]"
                )


@dataclass(frozen=True)
class QuestionnaireResponse:
    """Result of one administration of a ``Questionnaire`` (FHIR shape).

    ``responses`` is the raw answer map keyed by item code. ``scores`` carries
    instrument-specific aggregates (e.g. PHQ-9 ``total``, WOS-5 ``normalised_0_100``).
    ``derived`` is for free-form classifier output (e.g. ``stage_of_change``).
    ``crisis_reason`` is a short human-readable explanation when ``crisis_flag``
    is true so the operator UI can show *why* the case was escalated.
    """

    instrument_code: TriageInstrumentCode
    instrument_version: str
    responses: dict[str, int]
    scores: dict[str, Any]
    risk_level: TriageRiskLevel
    crisis_flag: bool = False
    crisis_reason: str | None = None
    derived: dict[str, Any] = field(default_factory=dict[str, Any])

    def __post_init__(self) -> None:
        if self.crisis_flag and not self.crisis_reason:
            raise ValueError("crisis_flag=True requires crisis_reason")
