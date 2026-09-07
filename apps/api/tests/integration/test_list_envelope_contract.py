"""Engagement and survey lists answer with the canonical envelope.

API-01 recorded that both routes returned a bare JSON array while the frontend
typed them as a paginated envelope and read `data.items`, which was undefined.
These drive the real routes against real PostgreSQL and assert the envelope,
the server-side filters, and that page two returns the next slice rather than
repeating page one.

Run with TEST_DATABASE_URL pointing at local PostgreSQL.
"""

from datetime import timedelta
from uuid import uuid4

import pytest_asyncio
from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient
from sqlalchemy.engine import make_url
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine
from sqlalchemy.pool import NullPool
from sqlalchemy.schema import CreateSchema, DropSchema

from app.api.routes.engagements import router as engagements_router
from app.api.routes.surveys import router as surveys_router
from app.core.database import get_db
from app.core.exception_handlers import register_exception_handlers
from app.core.security import TokenData, get_current_user
from app.domain.enums import (
    EngagementStatus,
    SubscriptionTier,
    SurveyCampaignStatus,
    SurveySource,
    TenantRole,
    TenantStatus,
)
from app.infrastructure.models.base import Base
from app.infrastructure.models.engagement_model import EngagementModel
from app.infrastructure.models.survey_model import SurveyCampaignModel
from app.infrastructure.models.tenant_model import TenantModel
from app.shared.utils.datetime import utc_now
from tests.integration._database_url import require_local_database

TENANT_ID = "tenant-list-envelope"
OTHER_TENANT_ID = "tenant-list-envelope-b"
USER_ID = "user-list-envelope"
ENGAGEMENT_COUNT = 25


def _engagements(now):
    for index in range(ENGAGEMENT_COUNT):
        created = now - timedelta(minutes=index)
        yield EngagementModel(
            id=f"engagement-list-{index:02d}",
            tenant_id=TENANT_ID,
            client_id="client-a" if index % 2 == 0 else "client-b",
            name=f"Engagement {index:02d}",
            description=None,
            status=EngagementStatus.ACTIVE if index % 2 == 0 else EngagementStatus.DRAFT,
            period_start=None,
            period_end=None,
            deliverables=[],
            hours_log=[],
            created_by=USER_ID,
            created_at=created,
            updated_at=created,
        )


def _campaign(index: int, tenant_id: str, now):
    created = now - timedelta(minutes=index)
    return SurveyCampaignModel(
        id=f"camp-{tenant_id[-1]}-{index:02d}",
        tenant_id=tenant_id,
        client_id="client-a",
        name=f"Campaign {index:02d}",
        source=SurveySource.GOOGLE_FORMS,
        external_form_id=f"form-{index:02d}",
        webhook_secret="s" * 32,
        status=SurveyCampaignStatus.ACTIVE if index % 2 == 0 else SurveyCampaignStatus.DRAFT,
        period_start=None,
        period_end=None,
        anonymous=True,
        response_count=index,
        created_by=USER_ID,
        created_at=created,
        updated_at=created,
    )


@pytest_asyncio.fixture
async def db():
    url = make_url(require_local_database("TEST_DATABASE_URL"))
    schema = "list_envelope_" + uuid4().hex
    admin = create_async_engine(url, poolclass=NullPool)
    async with admin.begin() as connection:
        await connection.execute(CreateSchema(schema))
    engine = create_async_engine(
        url, poolclass=NullPool, connect_args={"server_settings": {"search_path": schema}}
    )
    async with engine.begin() as connection:
        await connection.run_sync(Base.metadata.create_all)
    sessions = async_sessionmaker(engine, expire_on_commit=False)

    now = utc_now()
    async with sessions() as session:
        for tenant_id, code in ((TENANT_ID, "lista"), (OTHER_TENANT_ID, "listb")):
            session.add(
                TenantModel(
                    id=tenant_id,
                    name=f"List tenant {code}",
                    code=code,
                    settings={},
                    status=TenantStatus.ACTIVE,
                    subscription_tier=SubscriptionTier.FREE,
                )
            )
        await session.commit()
    async with sessions() as session:
        for model in _engagements(now):
            session.add(model)
        for index in range(3):
            session.add(_campaign(index, TENANT_ID, now))
        session.add(_campaign(0, OTHER_TENANT_ID, now))
        await session.commit()
    try:
        yield sessions
    finally:
        await engine.dispose()
        async with admin.begin() as connection:
            await connection.execute(DropSchema(schema, cascade=True))
        await admin.dispose()


@pytest_asyncio.fixture
async def api(db):
    app = FastAPI()
    register_exception_handlers(app)
    app.include_router(engagements_router)
    app.include_router(surveys_router)

    async def override_db():
        async with db() as session:
            yield session

    app.dependency_overrides[get_db] = override_db
    app.dependency_overrides[get_current_user] = lambda: TokenData(
        user_id=USER_ID, tenant_id=TENANT_ID, role=TenantRole.ADMIN.value
    )
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        yield client


class TestEngagementListEnvelope:
    async def test_the_first_page_carries_records_and_the_total(self, api):
        response = await api.get("/engagements", params={"limit": 10})
        assert response.status_code == 200, response.text
        body = response.json()
        assert body["total"] == ENGAGEMENT_COUNT
        assert body["page"] == 1
        assert body["limit"] == 10
        assert body["has_more"] is True
        assert len(body["items"]) == 10
        assert body["items"][0]["name"] == "Engagement 00"

    async def test_page_two_returns_the_next_slice(self, api):
        first = (await api.get("/engagements", params={"limit": 10})).json()
        second = (await api.get("/engagements", params={"limit": 10, "page": 2})).json()
        assert second["page"] == 2
        assert [item["id"] for item in second["items"]] != [item["id"] for item in first["items"]]
        assert second["items"][0]["name"] == "Engagement 10"

    async def test_the_last_page_reports_no_more(self, api):
        body = (await api.get("/engagements", params={"limit": 10, "page": 3})).json()
        assert len(body["items"]) == 5
        assert body["has_more"] is False

    async def test_the_status_filter_narrows_the_total_as_well_as_the_page(self, api):
        body = (await api.get("/engagements", params={"status": "Draft", "limit": 100})).json()
        assert body["total"] == 12
        assert {item["status"] for item in body["items"]} == {"Draft"}

    async def test_search_and_client_filters_are_applied_by_the_server(self, api):
        by_name = (await api.get("/engagements", params={"search": "ment 07"})).json()
        assert [item["name"] for item in by_name["items"]] == ["Engagement 07"]

        by_client = (
            await api.get("/engagements", params={"client_id": "client-b", "limit": 100})
        ).json()
        assert by_client["total"] == 12
        assert {item["client_id"] for item in by_client["items"]} == {"client-b"}

    async def test_ascending_sort_reverses_the_page(self, api):
        body = (
            await api.get(
                "/engagements", params={"sort_by": "name", "sort_desc": "false", "limit": 3}
            )
        ).json()
        assert [item["name"] for item in body["items"]] == [
            "Engagement 00",
            "Engagement 01",
            "Engagement 02",
        ]


class TestSurveyCampaignListEnvelope:
    async def test_the_envelope_carries_only_this_tenant_s_records(self, api):
        body = (await api.get("/survey-campaigns")).json()
        assert body["total"] == 3
        assert body["has_more"] is False
        assert {item["tenant_id"] for item in body["items"]} == {TENANT_ID}

    async def test_page_two_returns_the_next_slice(self, api):
        first = (await api.get("/survey-campaigns", params={"limit": 2})).json()
        second = (await api.get("/survey-campaigns", params={"limit": 2, "page": 2})).json()
        assert first["has_more"] is True
        assert len(second["items"]) == 1
        assert second["items"][0]["id"] not in [item["id"] for item in first["items"]]

    async def test_the_status_filter_narrows_the_total_as_well_as_the_page(self, api):
        body = (await api.get("/survey-campaigns", params={"status": "Draft"})).json()
        assert body["total"] == 1
        assert {item["status"] for item in body["items"]} == {"Draft"}

    async def test_the_list_never_returns_the_webhook_secret(self, api):
        body = (await api.get("/survey-campaigns")).json()
        assert all("webhook_secret" not in item for item in body["items"])
