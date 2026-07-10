"""Survey ingestion + aggregation use case tests (Phase 3 #D-Survey)."""

from datetime import UTC, datetime

import pytest

from app.application.use_cases.survey_use_cases import (
    GetSurveyAggregateUseCase,
    IngestSurveyResponseUseCase,
)
from app.core.webhook_signature import compute_signature
from app.domain.entities.survey_campaign import SurveyCampaign
from app.domain.entities.survey_response import SurveyResponse
from app.domain.enums import SurveyCampaignStatus, SurveySource
from app.domain.exceptions import DomainError, NotFoundError
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
            if (
                r.campaign_id == campaign_id
                and r.external_response_id == external_response_id
            ):
                return r
        return None

    async def list_for_campaign(self, tenant_id, campaign_id, *, limit=1000, offset=0):
        return [
            r
            for r in self.responses.values()
            if r.tenant_id == tenant_id and r.campaign_id == campaign_id
        ]


def _campaign(*, status=SurveyCampaignStatus.ACTIVE) -> SurveyCampaign:
    now = datetime.now(UTC)
    return SurveyCampaign(
        id=SurveyCampaignId("sc-1"),
        tenant_id=TenantId("t-1"),
        client_id=ClientId("client-1"),
        name="Q3",
        source=SurveySource.GOOGLE_FORMS,
        external_form_id="form-x",
        webhook_secret=SECRET,
        status=status,
        created_by=UserId("u-1"),
        created_at=now,
        updated_at=now,
        activated_at=now if status == SurveyCampaignStatus.ACTIVE else None,
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


class TestGetSurveyAggregate:
    @pytest.mark.asyncio
    async def test_aggregates_answer_frequencies(self):
        campaign = _campaign()
        campaigns = _FakeCampaignRepo(campaign)
        responses = _FakeResponseRepo()
        now = datetime.now(UTC)
        for i, q1 in enumerate(["yes", "yes", "no"]):
            responses.responses[f"r-{i}"] = SurveyResponse(
                id=SurveyResponseId(f"r-{i}"),
                tenant_id=TenantId("t-1"),
                campaign_id=SurveyCampaignId("sc-1"),
                external_response_id=f"ext-{i}",
                submitted_at=now,
                received_at=now,
                payload={"q1": q1, "score": 5},
            )
        out = await GetSurveyAggregateUseCase(campaigns, responses).execute(
            SurveyCampaignId("sc-1")
        )
        assert out["response_total"] == 3
        assert out["answer_frequencies"]["q1"] == {"yes": 2, "no": 1}
        assert out["answer_frequencies"]["score"] == {"5": 3}
        # Aggregate output never contains individual rows:
        assert "responses" not in out
