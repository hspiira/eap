"""Survey ingestion + aggregation use case tests (Phase 3 #D-Survey)."""

import json
from datetime import UTC, datetime

import pytest

from app.application.use_cases.survey_use_cases import (
    GetSurveyAggregateUseCase,
    IngestSurveyResponseUseCase,
)
from app.core.webhook_signature import compute_signature
from app.domain.entities.survey_campaign import ApprovedQuestion, SurveyCampaign
from app.domain.entities.survey_response import SurveyResponse
from app.domain.enums import SurveyCampaignStatus
from app.domain.exceptions import DomainError, NotFoundError
from app.domain.services.survey_disclosure import AnswerTally
from app.domain.value_objects.core import (
    ClientId,
    SurveyCampaignId,
    SurveyResponseId,
    TenantId,
    UserId,
)

SECRET = "x" * 40


class _FakeCampaignRepo:
    def __init__(self, campaign: SurveyCampaign | None = None):
        self.campaigns: dict[str, SurveyCampaign] = {}
        if campaign is not None:
            self.campaigns[campaign.id.value] = campaign

    async def get_by_id(self, entity_id):
        return self.campaigns.get(entity_id.value)

    async def save(self, entity):
        self.campaigns[entity.id.value] = entity

    async def delete(self, entity_id):
        self.campaigns.pop(entity_id.value, None)

    async def exists(self, entity_id):
        return entity_id.value in self.campaigns

    async def list_for_tenant(self, tenant_id, *, limit=50, offset=0):
        return [c for c in self.campaigns.values() if c.tenant_id == tenant_id]


class _FakeResponseRepo:
    def __init__(self):
        self.responses: dict[str, SurveyResponse] = {}

    async def get_by_id(self, entity_id):
        return self.responses.get(entity_id.value)

    async def save(self, entity):
        self.responses[entity.id.value] = entity

    async def delete(self, entity_id):
        self.responses.pop(entity_id.value, None)

    async def exists(self, entity_id):
        return entity_id.value in self.responses

    async def find_by_external_id(self, campaign_id, external_response_id):
        for r in self.responses.values():
            if r.campaign_id == campaign_id and r.external_response_id == external_response_id:
                return r
        return None

    async def list_for_campaign(self, tenant_id, campaign_id, *, limit=1000, offset=0):
        return [
            r
            for r in self.responses.values()
            if r.tenant_id == tenant_id and r.campaign_id == campaign_id
        ]


def _helpfulness() -> ApprovedQuestion:
    return ApprovedQuestion(
        key="q1",
        label="Was the service helpful?",
        choices=("Yes", "No", "Prefer not to say"),
    )


def _campaign(
    *,
    status=SurveyCampaignStatus.ACTIVE,
    approved_questions: list[ApprovedQuestion] | None = None,
) -> SurveyCampaign:
    now = datetime.now(UTC)
    return SurveyCampaign(
        id=SurveyCampaignId("sc-1"),
        tenant_id=TenantId("t-1"),
        client_id=ClientId("client-1"),
        name="Q3",
        source="GoogleForms",
        external_form_id="form-x",
        webhook_secret=SECRET,
        status=status,
        created_by=UserId("u-1"),
        created_at=now,
        updated_at=now,
        activated_at=now if status == SurveyCampaignStatus.ACTIVE else None,
        approved_questions=list(approved_questions or []),
    )


class TestIngestSurveyResponse:
    @pytest.mark.asyncio
    async def test_happy_path(self):
        campaigns = _FakeCampaignRepo(_campaign())
        responses = _FakeResponseRepo()
        use_case = IngestSurveyResponseUseCase(campaigns, responses)
        body = b'{"external_response_id":"e-1"}'
        sig = compute_signature(SECRET, body)
        record, fresh = await use_case.execute(
            campaign_id=SurveyCampaignId("sc-1"),
            signature_header=sig,
            raw_body=body,
            external_response_id="e-1",
            submitted_at=datetime.now(UTC),
            payload={"q1": "yes"},
        )
        assert fresh is True
        assert record.external_response_id == "e-1"
        assert len(responses.responses) == 1
        assert campaigns.campaigns["sc-1"].response_count == 1

    @pytest.mark.asyncio
    async def test_idempotent_replay(self):
        campaigns = _FakeCampaignRepo(_campaign())
        responses = _FakeResponseRepo()
        # Pre-existing response
        now = datetime.now(UTC)
        responses.responses["existing"] = SurveyResponse(
            id=SurveyResponseId("existing"),
            tenant_id=TenantId("t-1"),
            campaign_id=SurveyCampaignId("sc-1"),
            external_response_id="dup",
            submitted_at=now,
            received_at=now,
            payload={},
        )
        use_case = IngestSurveyResponseUseCase(campaigns, responses)
        body = b'{"external_response_id":"dup"}'
        sig = compute_signature(SECRET, body)
        record, fresh = await use_case.execute(
            campaign_id=SurveyCampaignId("sc-1"),
            signature_header=sig,
            raw_body=body,
            external_response_id="dup",
            submitted_at=now,
            payload={"new": "data"},
        )
        assert fresh is False
        assert record.id.value == "existing"
        assert len(responses.responses) == 1
        # Original payload preserved (not overwritten by replay):
        assert record.payload == {}
        assert campaigns.campaigns["sc-1"].response_count == 0

    @pytest.mark.asyncio
    async def test_invalid_signature_rejected(self):
        campaigns = _FakeCampaignRepo(_campaign())
        responses = _FakeResponseRepo()
        use_case = IngestSurveyResponseUseCase(campaigns, responses)
        body = b'{"external_response_id":"e-1"}'
        with pytest.raises(IngestSurveyResponseUseCase.SignatureInvalid):
            await use_case.execute(
                campaign_id=SurveyCampaignId("sc-1"),
                signature_header="deadbeef",
                raw_body=body,
                external_response_id="e-1",
                submitted_at=datetime.now(UTC),
                payload={},
            )

    @pytest.mark.asyncio
    async def test_unknown_campaign(self):
        campaigns = _FakeCampaignRepo()
        responses = _FakeResponseRepo()
        use_case = IngestSurveyResponseUseCase(campaigns, responses)
        with pytest.raises(NotFoundError):
            await use_case.execute(
                campaign_id=SurveyCampaignId("nope"),
                signature_header="x",
                raw_body=b"{}",
                external_response_id="e-1",
                submitted_at=datetime.now(UTC),
                payload={},
            )

    @pytest.mark.asyncio
    async def test_draft_campaign_rejects_responses(self):
        campaigns = _FakeCampaignRepo(_campaign(status=SurveyCampaignStatus.DRAFT))
        responses = _FakeResponseRepo()
        use_case = IngestSurveyResponseUseCase(campaigns, responses)
        body = b'{"external_response_id":"e-1"}'
        sig = compute_signature(SECRET, body)
        with pytest.raises(DomainError, match="not accepting"):
            await use_case.execute(
                campaign_id=SurveyCampaignId("sc-1"),
                signature_header=sig,
                raw_body=body,
                external_response_id="e-1",
                submitted_at=datetime.now(UTC),
                payload={},
            )


class _FakeTallyReader:
    """Stands in for the SQL reader; records which questions it was asked about."""

    def __init__(self, counts: dict[str, AnswerTally], total: int = 0):
        self._counts = counts
        self._total = total
        self.asked: list[str] = []

    async def count_responses(self, *, tenant_id, campaign_id, since=None, until=None):
        return self._total

    async def tally(self, *, tenant_id, campaign_id, question, since=None, until=None):
        self.asked.append(question.key)
        return self._counts.get(question.key, AnswerTally())


class TestGetSurveyAggregate:
    @pytest.mark.asyncio
    async def test_counts_the_approved_choices(self):
        campaign = _campaign(approved_questions=[_helpfulness()])
        reader = _FakeTallyReader({"q1": AnswerTally(counts={"Yes": 7, "No": 5})}, total=12)
        out = await GetSurveyAggregateUseCase(_FakeCampaignRepo(campaign), reader).execute(
            SurveyCampaignId("sc-1")
        )
        assert out["response_total"] == 12
        assert out["answer_frequencies"]["q1"] == {"Yes": 7, "No": 5, "Prefer not to say": "<5"}
        assert out["question_labels"] == {"q1": "Was the service helpful?"}
        assert out["disclosure_status"] == "ok"

    @pytest.mark.asyncio
    async def test_a_free_text_question_is_never_counted(self):
        """PRIV-01: an unapproved question is not asked about and not reported."""
        campaign = _campaign(approved_questions=[_helpfulness()])
        reader = _FakeTallyReader({}, total=12)
        out = await GetSurveyAggregateUseCase(_FakeCampaignRepo(campaign), reader).execute(
            SurveyCampaignId("sc-1")
        )
        assert reader.asked == ["q1"]
        assert "comment" not in out["answer_frequencies"]
        assert "comment" not in json.dumps(out)

    @pytest.mark.asyncio
    async def test_a_campaign_without_approved_questions_reports_that(self):
        campaign = _campaign()
        reader = _FakeTallyReader({}, total=3)
        out = await GetSurveyAggregateUseCase(_FakeCampaignRepo(campaign), reader).execute(
            SurveyCampaignId("sc-1")
        )
        assert out["disclosure_status"] == "no_approved_questions"
        assert out["answer_frequencies"] == {}

    @pytest.mark.asyncio
    async def test_a_small_cohort_total_is_suppressed(self):
        """PRIV-01: the total obeys the same floor as the cells."""
        campaign = _campaign(approved_questions=[_helpfulness()])
        reader = _FakeTallyReader({"q1": AnswerTally(counts={"Yes": 1})}, total=1)
        out = await GetSurveyAggregateUseCase(_FakeCampaignRepo(campaign), reader).execute(
            SurveyCampaignId("sc-1")
        )
        assert out["response_total"] == "<5"
        assert out["answer_frequencies"]["q1"]["Yes"] == "<5"

    @pytest.mark.asyncio
    async def test_off_list_answers_are_counted_but_not_disclosed(self):
        campaign = _campaign(approved_questions=[_helpfulness()])
        reader = _FakeTallyReader({"q1": AnswerTally(counts={"Yes": 9}, unapproved=6)}, total=15)
        out = await GetSurveyAggregateUseCase(_FakeCampaignRepo(campaign), reader).execute(
            SurveyCampaignId("sc-1")
        )
        assert out["unapproved_answers"] == {"q1": 6}

    @pytest.mark.asyncio
    async def test_unknown_campaign(self):
        with pytest.raises(NotFoundError):
            await GetSurveyAggregateUseCase(_FakeCampaignRepo(), _FakeTallyReader({})).execute(
                SurveyCampaignId("nope")
            )
