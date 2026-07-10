"""Survey campaign FSM + response invariants (Phase 3 #D-Survey)."""

from datetime import UTC, date, datetime

import pytest

from app.domain.entities.survey_campaign import SurveyCampaign
from app.domain.entities.survey_response import SurveyResponse
from app.domain.enums import SurveyCampaignStatus, SurveySource
from app.domain.events import (
    SurveyCampaignActivated,
    SurveyCampaignClosed,
    SurveyCampaignCreated,
    SurveyResponseIngested,
)
from app.domain.exceptions import DomainError, InvalidStateError
from app.domain.value_objects.core import (
    ClientId,
    SurveyCampaignId,
    SurveyResponseId,
    TenantId,
    UserId,
)


def _campaign(
    *, status: SurveyCampaignStatus = SurveyCampaignStatus.DRAFT
) -> SurveyCampaign:
    now = datetime.now(UTC)
    return SurveyCampaign(
        id=SurveyCampaignId("sc-1"),
        tenant_id=TenantId("t-1"),
        client_id=ClientId("client-1"),
        name="ABSA quarterly satisfaction",
        source=SurveySource.GOOGLE_FORMS,
        external_form_id="1FAIpQLSeXyz",
        webhook_secret="x" * 40,
        status=status,
        created_by=UserId("u-1"),
        created_at=now,
        updated_at=now,
        period_start=date(2026, 7, 1),
        period_end=date(2026, 9, 30),
    )


class TestSurveyCampaignCreation:
    def test_creation_emits_event(self):
        c = _campaign()
        assert any(isinstance(e, SurveyCampaignCreated) for e in c.events)

    def test_short_secret_rejected(self):
        now = datetime.now(UTC)
        with pytest.raises(DomainError, match="webhook_secret"):
            SurveyCampaign(
                id=SurveyCampaignId("sc-x"),
                tenant_id=TenantId("t-1"),
                client_id=ClientId("c-1"),
                name="x",
                source=SurveySource.GOOGLE_FORMS,
                external_form_id="f",
                webhook_secret="too-short",
                status=SurveyCampaignStatus.DRAFT,
                created_by=UserId("u-1"),
                created_at=now,
                updated_at=now,
            )

    def test_period_invariant(self):
        now = datetime.now(UTC)
        with pytest.raises(DomainError, match="period_end"):
            SurveyCampaign(
                id=SurveyCampaignId("sc-x"),
                tenant_id=TenantId("t-1"),
                client_id=ClientId("c-1"),
                name="x",
                source=SurveySource.GOOGLE_FORMS,
                external_form_id="f",
                webhook_secret="x" * 40,
                status=SurveyCampaignStatus.DRAFT,
                created_by=UserId("u-1"),
                created_at=now,
                updated_at=now,
                period_start=date(2026, 9, 1),
                period_end=date(2026, 8, 1),
            )

    def test_external_form_id_required(self):
        now = datetime.now(UTC)
        with pytest.raises(DomainError):
            SurveyCampaign(
                id=SurveyCampaignId("sc-x"),
                tenant_id=TenantId("t-1"),
                client_id=ClientId("c-1"),
                name="x",
                source=SurveySource.GOOGLE_FORMS,
                external_form_id="",
                webhook_secret="x" * 40,
                status=SurveyCampaignStatus.DRAFT,
                created_by=UserId("u-1"),
                created_at=now,
                updated_at=now,
            )


class TestSurveyCampaignFSM:
    def test_activate_from_draft(self):
        c = _campaign()
        c.activate()
        assert c.status == SurveyCampaignStatus.ACTIVE
        assert c.activated_at is not None
        assert any(isinstance(e, SurveyCampaignActivated) for e in c.events)
        assert c.is_accepting_responses() is True

    def test_close_from_active(self):
        c = _campaign()
        c.activate()
        c.close()
        assert c.status == SurveyCampaignStatus.CLOSED
        assert c.closed_at is not None
        assert any(isinstance(e, SurveyCampaignClosed) for e in c.events)
        assert c.is_accepting_responses() is False

    def test_cannot_activate_active(self):
        c = _campaign()
        c.activate()
        with pytest.raises(InvalidStateError):
            c.activate()

    def test_cannot_close_draft(self):
        c = _campaign()
        with pytest.raises(InvalidStateError):
            c.close()

    def test_cannot_activate_closed(self):
        c = _campaign(status=SurveyCampaignStatus.CLOSED)
        with pytest.raises(InvalidStateError):
            c.activate()

    def test_increment_response_count(self):
        c = _campaign()
        c.activate()
        c.increment_response_count()
        c.increment_response_count()
        assert c.response_count == 2


class TestSurveyResponseInvariants:
    def test_creation_emits_ingestion_event(self):
        now = datetime.now(UTC)
        r = SurveyResponse(
            id=SurveyResponseId("r-1"),
            tenant_id=TenantId("t-1"),
            campaign_id=SurveyCampaignId("sc-1"),
            external_response_id="ext-1",
            submitted_at=now,
            received_at=now,
            payload={"q1": "yes"},
        )
        assert any(isinstance(e, SurveyResponseIngested) for e in r.events)

    def test_external_id_required(self):
        now = datetime.now(UTC)
        with pytest.raises(DomainError):
            SurveyResponse(
                id=SurveyResponseId("r-1"),
                tenant_id=TenantId("t-1"),
                campaign_id=SurveyCampaignId("sc-1"),
                external_response_id="",
                submitted_at=now,
                received_at=now,
                payload={},
            )

    def test_naive_submitted_at_rejected(self):
        from datetime import datetime as dt

        with pytest.raises(DomainError, match="timezone"):
            SurveyResponse(
                id=SurveyResponseId("r-1"),
                tenant_id=TenantId("t-1"),
                campaign_id=SurveyCampaignId("sc-1"),
                external_response_id="ext-1",
                submitted_at=dt(2026, 5, 8, 12, 0, 0),
                received_at=datetime.now(UTC),
                payload={},
            )
