"""The survey aggregate counts approved choices, over the whole campaign.

Two findings meet here. PRIV-01: a synthetic name, a phone-like value and a
narrative answer are stored in the raw payload and must not appear anywhere in
the aggregate. DATA-01: the total used to be the length of a 10,000-row page,
so a campaign with more responses than that reported the page size as its
population.

Run with TEST_DATABASE_URL pointing at local PostgreSQL.
"""

import json
from datetime import UTC, datetime
from uuid import uuid4

import pytest_asyncio
from sqlalchemy.engine import make_url
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine
from sqlalchemy.pool import NullPool
from sqlalchemy.schema import CreateSchema, DropSchema

from app.application.use_cases.survey_use_cases import GetSurveyAggregateUseCase
from app.domain.enums import (
    SubscriptionTier,
    SurveyCampaignStatus,
    TenantStatus,
)
from app.domain.value_objects.core import SurveyCampaignId
from app.infrastructure.models.base import Base
from app.infrastructure.models.survey_model import SurveyCampaignModel, SurveyResponseModel
from app.infrastructure.models.survey_source_model import SurveySourceModel
from app.infrastructure.models.tenant_model import TenantModel
from app.infrastructure.repositories.survey_repository import SurveyCampaignRepositoryImpl
from app.infrastructure.services.survey_aggregation import SurveyAnswerTallyReaderImpl
from app.shared.utils.datetime import utc_now
from tests.integration._database_url import require_local_database

TENANT = "tenant-survey"
CAMPAIGN = "campaign-survey"
LARGE_CAMPAIGN = "campaign-large"
SUBMITTED = datetime(2026, 1, 10, 9, 0, tzinfo=UTC)

IDENTIFYING_NAME = "Nakato Birungi"
PHONE_LIKE = "+256 772 000 111"
NARRATIVE = "My line manager shouted at me in front of the team on Tuesday."

APPROVED = [
    {
        "key": "helpful",
        "label": "Was the service helpful?",
        "choices": ["Yes", "No", "Prefer not to say"],
    }
]


@pytest_asyncio.fixture
async def db():
    url = make_url(require_local_database("TEST_DATABASE_URL"))
    schema = "survey_disclosure_" + uuid4().hex
    admin = create_async_engine(url, poolclass=NullPool)
    async with admin.begin() as connection:
        await connection.execute(CreateSchema(schema))
    engine = create_async_engine(
        url, poolclass=NullPool, connect_args={"server_settings": {"search_path": schema}}
    )
    async with engine.begin() as connection:
        await connection.run_sync(Base.metadata.create_all)
    sessions = async_sessionmaker(engine, expire_on_commit=False)
    try:
        async with sessions() as session:
            await _seed(session)
        yield sessions
    finally:
        await engine.dispose()
        async with admin.begin() as connection:
            await connection.execute(DropSchema(schema, cascade=True))
        await admin.dispose()


def _campaign(campaign_id: str, now: datetime) -> SurveyCampaignModel:
    return SurveyCampaignModel(
        id=campaign_id,
        tenant_id=TENANT,
        client_id="client-1",
        name=campaign_id,
        source="GoogleForms",
        external_form_id="form",
        webhook_secret="x" * 40,
        status=SurveyCampaignStatus.ACTIVE,
        anonymous=True,
        approved_questions=APPROVED,
        response_count=0,
        created_by="user-1",
        created_at=now,
        updated_at=now,
    )


async def _seed(session) -> None:
    # Own schema, so the reference row the campaign's source points at has to be
    # seeded here: source is a foreign key now, not an enum value.
    session.add(SurveySourceModel(code="GoogleForms", name="Google Forms"))
    now = utc_now()
    session.add(
        TenantModel(
            id=TENANT,
            name="Survey tenant",
            code="svy",
            settings={},
            status=TenantStatus.ACTIVE,
            subscription_tier=SubscriptionTier.FREE,
        )
    )
    await session.commit()
    session.add(_campaign(CAMPAIGN, now))
    session.add(_campaign(LARGE_CAMPAIGN, now))
    await session.commit()

    answers = ["Yes"] * 8 + ["No"] * 6 + ["Maybe, when I could get through"] * 2
    for index, answer in enumerate(answers):
        session.add(
            SurveyResponseModel(
                id=f"r-{index}",
                tenant_id=TENANT,
                campaign_id=CAMPAIGN,
                external_response_id=f"ext-{index}",
                submitted_at=SUBMITTED,
                received_at=now,
                payload={
                    "helpful": answer,
                    "name": IDENTIFYING_NAME,
                    "phone": PHONE_LIKE,
                    "comment": NARRATIVE,
                },
                created_at=now,
                updated_at=now,
            )
        )
    await session.commit()

    await session.execute(
        SurveyResponseModel.__table__.insert(),
        [
            {
                "id": f"big-{index}",
                "tenant_id": TENANT,
                "campaign_id": LARGE_CAMPAIGN,
                "external_response_id": f"big-ext-{index}",
                "submitted_at": SUBMITTED,
                "received_at": now,
                "payload": {"helpful": "Yes" if index % 2 else "No"},
                "metrics": None,
                "created_at": now,
                "updated_at": now,
            }
            for index in range(10_001)
        ],
    )
    await session.commit()


async def _aggregate(db, campaign_id: str, *, floor: int = 5) -> dict:
    async with db() as session:
        use_case = GetSurveyAggregateUseCase(
            SurveyCampaignRepositoryImpl(session),
            SurveyAnswerTallyReaderImpl(session),
            min_cell_size=floor,
        )
        return await use_case.execute(SurveyCampaignId(campaign_id))


class TestFreeTextNeverReachesTheAggregate:
    async def test_a_synthetic_name_is_absent(self, db):
        assert IDENTIFYING_NAME not in json.dumps(await _aggregate(db, CAMPAIGN))

    async def test_a_phone_like_value_is_absent(self, db):
        assert PHONE_LIKE not in json.dumps(await _aggregate(db, CAMPAIGN))

    async def test_a_narrative_answer_is_absent(self, db):
        assert NARRATIVE not in json.dumps(await _aggregate(db, CAMPAIGN))

    async def test_unapproved_questions_are_not_even_named(self, db):
        result = await _aggregate(db, CAMPAIGN)
        assert set(result["answer_frequencies"]) == {"helpful"}

    async def test_an_off_list_answer_is_counted_without_its_text(self, db):
        result = await _aggregate(db, CAMPAIGN, floor=1)
        assert result["unapproved_answers"]["helpful"] == 2
        assert "Maybe" not in json.dumps(result)


class TestApprovedChoicesAreStillReported:
    async def test_the_approved_choices_are_counted(self, db):
        result = await _aggregate(db, CAMPAIGN)
        assert result["answer_frequencies"]["helpful"]["Yes"] == 8
        assert result["answer_frequencies"]["helpful"]["No"] == 6

    async def test_a_choice_nobody_picked_is_reported_as_suppressed(self, db):
        result = await _aggregate(db, CAMPAIGN)
        assert result["answer_frequencies"]["helpful"]["Prefer not to say"] == "<5"

    async def test_the_question_label_comes_from_the_campaign(self, db):
        result = await _aggregate(db, CAMPAIGN)
        assert result["question_labels"]["helpful"] == "Was the service helpful?"


class TestTotalsBeyondTheOldPageLimit:
    async def test_a_campaign_over_ten_thousand_responses_is_counted_exactly(self, db):
        """DATA-01: the total is the campaign's, not the old 10,000-row page."""
        result = await _aggregate(db, LARGE_CAMPAIGN)
        assert result["response_total"] == 10_001

    async def test_the_frequencies_cover_every_response(self, db):
        result = await _aggregate(db, LARGE_CAMPAIGN)
        counts = result["answer_frequencies"]["helpful"]
        assert counts["Yes"] + counts["No"] == 10_001
