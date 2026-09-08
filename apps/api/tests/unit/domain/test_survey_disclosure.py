"""The employer-facing survey aggregate discloses approved choices and nothing else.

Counting a free-text answer republishes it, so the policy is a list of approved
questions with closed answer lists rather than a filter over whatever a form
happened to collect (MODULES_REPAIR_PLAN PRIV-01).
"""

import json

import pytest

from app.domain.entities.survey_campaign import ApprovedQuestion
from app.domain.exceptions import DomainError
from app.domain.services.survey_disclosure import AnswerTally, aggregate_payload

HELPFUL = ApprovedQuestion(
    key="helpful",
    label="Was the service helpful?",
    choices=("Yes", "No", "Prefer not to say"),
)


class TestApprovedQuestion:
    def test_a_question_needs_a_closed_choice_list(self):
        with pytest.raises(DomainError, match="at least one choice"):
            ApprovedQuestion(key="comment", label="Comments", choices=())

    def test_duplicate_choices_are_rejected(self):
        with pytest.raises(DomainError, match="duplicate choices"):
            ApprovedQuestion(key="q", label="Q", choices=("Yes", "Yes"))


class TestAggregatePayload:
    def test_every_approved_choice_appears_even_at_zero(self):
        payload = aggregate_payload(
            questions=[HELPFUL],
            tallies={"helpful": AnswerTally(counts={"Yes": 9})},
            response_total=9,
        )
        assert set(payload["answer_frequencies"]["helpful"]) == set(HELPFUL.choices)

    def test_a_sub_floor_cell_is_suppressed(self):
        payload = aggregate_payload(
            questions=[HELPFUL],
            tallies={"helpful": AnswerTally(counts={"Yes": 9, "No": 2})},
            response_total=11,
        )
        assert payload["answer_frequencies"]["helpful"]["Yes"] == 9
        assert payload["answer_frequencies"]["helpful"]["No"] == "<5"

    def test_a_sub_floor_total_is_suppressed(self):
        payload = aggregate_payload(questions=[HELPFUL], tallies={}, response_total=3)
        assert payload["response_total"] == "<5"

    def test_an_unapproved_answer_is_counted_but_never_quoted(self):
        payload = aggregate_payload(
            questions=[HELPFUL],
            tallies={"helpful": AnswerTally(counts={"Yes": 9}, unapproved=7)},
            response_total=16,
        )
        assert payload["unapproved_answers"]["helpful"] == 7
        assert "Yes" in json.dumps(payload)

    def test_a_campaign_with_no_approved_questions_says_so(self):
        payload = aggregate_payload(questions=[], tallies={}, response_total=40)
        assert payload["disclosure_status"] == "no_approved_questions"
        assert payload["answer_frequencies"] == {}
        assert payload["response_total"] == 40

    def test_the_payload_never_contains_an_answer_outside_the_approved_list(self):
        """A tally that leaked an off-list value cannot reach the output."""
        payload = aggregate_payload(
            questions=[HELPFUL],
            tallies={
                "helpful": AnswerTally(
                    counts={"Yes": 9, "Wamala 0772 000 111, feeling suicidal": 6}
                )
            },
            response_total=15,
        )
        assert "Wamala" not in json.dumps(payload)


class TestAnswerTally:
    def test_merging_adds_counts_across_campaigns(self):
        merged = AnswerTally(counts={"Yes": 2}, unapproved=1).merged_with(
            AnswerTally(counts={"Yes": 3, "No": 4}, unapproved=2)
        )
        assert merged.counts == {"Yes": 5, "No": 4}
        assert merged.unapproved == 3
