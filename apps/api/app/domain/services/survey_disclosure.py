"""Disclosure policy for employer-facing survey aggregates.

Counting a free-text answer does not make it anonymous: a frequency table keyed
by the answer text republishes the text. Aggregates therefore report only the
campaign's approved questions and, within them, only the approved choices.
Anything else is counted as an unapproved answer and its text is discarded.

Counts and totals then go through the same small-cell floor as every other
employer-facing aggregate, so a cohort of one is never reported as one.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Protocol

from app.domain.entities.survey_campaign import ApprovedQuestion
from app.domain.services.cell_suppression import (
    DEFAULT_MIN_CELL_SIZE,
    suppress_count,
)


@dataclass(frozen=True)
class AnswerTally:
    """Counts for one approved question over one campaign."""

    counts: dict[str, int] = field(default_factory=dict[str, int])
    unapproved: int = 0

    def merged_with(self, other: AnswerTally) -> AnswerTally:
        counts = dict(self.counts)
        for choice, count in other.counts.items():
            counts[choice] = counts.get(choice, 0) + count
        return AnswerTally(counts=counts, unapproved=self.unapproved + other.unapproved)


class SurveyAnswerTallyReader(Protocol):
    """Read port for counting answers without loading response rows."""

    async def count_responses(
        self,
        *,
        tenant_id: str,
        campaign_id: str,
        since: datetime | None = None,
        until: datetime | None = None,
    ) -> int: ...

    async def tally(
        self,
        *,
        tenant_id: str,
        campaign_id: str,
        question: ApprovedQuestion,
        since: datetime | None = None,
        until: datetime | None = None,
    ) -> AnswerTally: ...


def disclosed_frequencies(
    questions: list[ApprovedQuestion],
    tallies: dict[str, AnswerTally],
    *,
    floor: int = DEFAULT_MIN_CELL_SIZE,
) -> dict[str, dict[str, int | str]]:
    """Frequency tables keyed by approved question, with every cell suppressed.

    Every approved choice appears, including the ones nobody picked, so a
    missing bar is not confused with a suppressed one.
    """
    out: dict[str, dict[str, int | str]] = {}
    for question in questions:
        tally = tallies.get(question.key, AnswerTally())
        out[question.key] = {
            choice: suppress_count(tally.counts.get(choice, 0), floor=floor)
            for choice in question.choices
        }
    return out


def unapproved_answer_counts(
    questions: list[ApprovedQuestion],
    tallies: dict[str, AnswerTally],
    *,
    floor: int = DEFAULT_MIN_CELL_SIZE,
) -> dict[str, int | str]:
    """Per question, how many answers fell outside the approved choices.

    Reported so a short frequency table is not read as low response when it is
    really an off-list answer set. The answers themselves are never returned.
    """
    return {
        question.key: suppress_count(
            tallies.get(question.key, AnswerTally()).unapproved, floor=floor
        )
        for question in questions
    }


def aggregate_payload(
    *,
    questions: list[ApprovedQuestion],
    tallies: dict[str, AnswerTally],
    response_total: int,
    floor: int = DEFAULT_MIN_CELL_SIZE,
) -> dict[str, Any]:
    """The employer-facing aggregate body shared by the campaign and report paths."""
    return {
        "disclosure_status": "ok" if questions else "no_approved_questions",
        "question_labels": {q.key: q.label for q in questions},
        "answer_frequencies": disclosed_frequencies(questions, tallies, floor=floor),
        "unapproved_answers": unapproved_answer_counts(questions, tallies, floor=floor),
        "response_total": suppress_count(response_total, floor=floor),
        "min_cell_size": floor,
    }
