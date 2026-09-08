"""Every report section applies the same client, period and deletion scope.

Reproduces MODULES_REPAIR_PLAN REP-02 against PostgreSQL: two clients, records
just inside and just outside the window, an afternoon record on the last day,
soft-deleted records, and a timezone boundary. Before the repair the sessions
and diagnosis sections ignored the client scope, sessions kept soft-deleted
rows, the end date cut the last day off at midnight, and the callback and
satisfaction sections applied no period at all.

Run with TEST_DATABASE_URL pointing at local PostgreSQL.
"""

from datetime import UTC, date, datetime
from uuid import uuid4

import pytest
import pytest_asyncio
from sqlalchemy import text
from sqlalchemy.engine import make_url
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine
from sqlalchemy.pool import NullPool
from sqlalchemy.schema import CreateSchema, DropSchema

from app.domain.entities.report import TemplateSection
from app.domain.enums import (
    AccreditationStatus,
    BaseStatus,
    CareCallbackCampaignStatus,
    ContractStatus,
    OutreachStatus,
    PanelStatus,
    PaymentFrequency,
    PaymentStatus,
    ProviderIdentityProvenance,
    ProviderTier,
    ReportQueryType,
    SessionAttendance,
    SessionDeliveryContext,
    SessionStatus,
    SubscriptionTier,
    SurveyCampaignStatus,
    TenantStatus,
    UgandaRegion,
)
from app.domain.exceptions import DomainError
from app.infrastructure.models.base import Base
from app.infrastructure.models.care_callback_model import (
    CareCallbackCampaignModel,
    OutreachRecordModel,
)
from app.infrastructure.models.client_model import ClientModel
from app.infrastructure.models.contract_model import ContractModel
from app.infrastructure.models.diagnosis_model import DiagnosisTypeModel
from app.infrastructure.models.provider_model import ProviderModel
from app.infrastructure.models.service_session_model import ServiceSessionModel
from app.infrastructure.models.survey_model import SurveyCampaignModel, SurveyResponseModel
from app.infrastructure.models.survey_source_model import SurveySourceModel
from app.infrastructure.models.tenant_model import TenantModel
from app.infrastructure.models.utilisation_event_model import UtilisationEventModel
from app.infrastructure.models.utilisation_event_type_model import UtilisationEventTypeModel
from app.infrastructure.services.report_query_runner import ReportQueryRunner
from app.shared.utils.datetime import utc_now
from tests.integration._database_url import require_local_database

TENANT = "tenant-report"
PROVIDER = "provider-report"
CLIENT_A = "client-a"
CLIENT_B = "client-b"
PERIOD = {"from": "2026-01-01", "to": "2026-01-31"}


def _at(text_value: str) -> datetime:
    return datetime.fromisoformat(text_value).replace(tzinfo=UTC)


@pytest_asyncio.fixture
async def db():
    url = make_url(require_local_database("TEST_DATABASE_URL"))
    schema = "report_scope_" + uuid4().hex
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


async def _seed(session) -> None:
    now = utc_now()
    # This module builds its own schema, so the reference rows the fixtures
    # point at have to be seeded here too: source and event type are foreign
    # keys now, not enum values.
    session.add(SurveySourceModel(code="GoogleForms", name="Google Forms"))
    session.add(UtilisationEventTypeModel(code="SessionDelivered", name="Session delivered"))
    session.add(
        TenantModel(
            id=TENANT,
            name="Report tenant",
            code="rpt",
            settings={},
            status=TenantStatus.ACTIVE,
            subscription_tier=SubscriptionTier.FREE,
        )
    )
    await session.commit()

    for client_id, name, code in ((CLIENT_A, "Client A", "CLA"), (CLIENT_B, "Client B", "CLB")):
        session.add(
            ClientModel(
                id=client_id,
                tenant_id=TENANT,
                name=name,
                code=code,
                contact_info={},
                status=BaseStatus.ACTIVE,
                created_at=now,
                updated_at=now,
            )
        )
    session.add(
        ProviderModel(
            id=PROVIDER,
            tenant_id=TENANT,
            user_id=None,
            display_name="Counsellor",
            identity_provenance=ProviderIdentityProvenance.OWNED,
            status=BaseStatus.ACTIVE,
            provider_profile={
                "tier": ProviderTier.T1.value,
                "region": UgandaRegion.CENTRAL.value,
                "accreditation_status": AccreditationStatus.ACCREDITED.value,
                "panel_status": PanelStatus.ACTIVE.value,
            },
            created_at=now,
            updated_at=now,
        )
    )
    session.add(DiagnosisTypeModel(id="dx-stress", code="STRESS", name="Work stress"))
    session.add(DiagnosisTypeModel(id="dx-grief", code="GRIEF", name="Loss and grief"))
    await session.commit()

    for member, client_id in (("member-a", CLIENT_A), ("member-b", CLIENT_B)):
        await session.execute(
            text(
                "INSERT INTO eligible_members (id, tenant_id, client_id, employer_member_id,"
                " relation, status, created_at, updated_at)"
                " VALUES (:id, :tenant, :client, :id, 'Employee', 'Active', now(), now())"
            ),
            {"id": member, "tenant": TENANT, "client": client_id},
        )
    await session.commit()

    await _seed_sessions(session, now)
    await _seed_contracts(session, now)
    await _seed_callbacks(session, now)
    await _seed_surveys(session, now)


async def _seed_sessions(session, now: datetime) -> None:
    # A session carries its own client, and attendance is coupled to whether it
    # names a member: both became required after this test was written.
    client_of = {"member-a": CLIENT_A, "member-b": CLIENT_B}
    rows = [
        ("s-in-first", "member-a", "2026-01-01T09:00:00", "dx-stress", None),
        ("s-in-last-pm", "member-a", "2026-01-31T15:00:00", "dx-stress", None),
        ("s-in-late-utc", "member-a", "2026-01-31T22:00:00", None, None),
        ("s-before", "member-a", "2025-12-31T23:00:00", "dx-stress", None),
        ("s-after", "member-a", "2026-02-01T00:30:00", "dx-stress", None),
        ("s-deleted", "member-a", "2026-01-15T10:00:00", "dx-stress", now),
        ("s-other-client", "member-b", "2026-01-15T10:00:00", "dx-grief", None),
    ]
    for session_id, member, when, diagnosis, deleted_at in rows:
        session.add(
            ServiceSessionModel(
                id=session_id,
                tenant_id=TENANT,
                service_id="svc-1",
                provider_id=PROVIDER,
                client_id=client_of[member],
                member_id=member,
                attendance=SessionAttendance.INDIVIDUAL,
                scheduled_at=_at(when),
                delivery_context=SessionDeliveryContext.DIRECT,
                status=SessionStatus.COMPLETED,
                reschedule_count=0,
                diagnosis_type_id=diagnosis,
                deleted_at=deleted_at,
                created_at=now,
                updated_at=now,
            )
        )
    await session.commit()


async def _seed_contracts(session, now: datetime) -> None:
    contracts = [
        ("contract-a", CLIENT_A, None),
        ("contract-b", CLIENT_B, None),
        ("contract-a-retired", CLIENT_A, now),
    ]
    for contract_id, client_id, deleted_at in contracts:
        session.add(
            ContractModel(
                id=contract_id,
                tenant_id=TENANT,
                client_id=client_id,
                start_date=date(2025, 6, 1),
                end_date=date(2026, 5, 31),
                billing_rate={"amount": 1, "currency": "UGX"},
                payment_frequency=PaymentFrequency.MONTHLY,
                payment_status=PaymentStatus.PENDING,
                status=ContractStatus.ACTIVE,
                deleted_at=deleted_at,
                created_at=now,
                updated_at=now,
            )
        )
    await session.commit()

    events = [
        ("u-in-first", "contract-a", date(2026, 1, 1), 5),
        ("u-in-last", "contract-a", date(2026, 1, 31), 3),
        ("u-before", "contract-a", date(2025, 12, 31), 90),
        ("u-other-client", "contract-b", date(2026, 1, 10), 40),
        ("u-retired", "contract-a-retired", date(2026, 1, 10), 70),
    ]
    for event_id, contract_id, occurred_on, units in events:
        session.add(
            UtilisationEventModel(
                id=event_id,
                tenant_id=TENANT,
                contract_id=contract_id,
                event_type="SessionDelivered",
                occurred_on=occurred_on,
                units=units,
                created_at=now,
                updated_at=now,
            )
        )
    await session.commit()


async def _seed_callbacks(session, now: datetime) -> None:
    campaigns = [
        ("wave-a", CLIENT_A, date(2026, 1, 5)),
        ("wave-b", CLIENT_B, date(2026, 1, 6)),
        ("wave-a-old", CLIENT_A, date(2025, 6, 1)),
    ]
    for campaign_id, client_id, period_start in campaigns:
        session.add(
            CareCallbackCampaignModel(
                id=campaign_id,
                tenant_id=TENANT,
                client_id=client_id,
                name=campaign_id,
                period_start=period_start,
                period_end=period_start,
                target_count=0,
                completed_count=0,
                counsellor_pool=[],
                status=CareCallbackCampaignStatus.ACTIVE,
                created_by="user-1",
                created_at=now,
                updated_at=now,
            )
        )
    await session.commit()

    records = [
        ("o-a-1", "wave-a", OutreachStatus.COMPLETED, True),
        ("o-a-2", "wave-a", OutreachStatus.COMPLETED, False),
        ("o-a-3", "wave-a", OutreachStatus.PENDING, False),
        ("o-b-1", "wave-b", OutreachStatus.COMPLETED, True),
        ("o-old-1", "wave-a-old", OutreachStatus.COMPLETED, True),
        ("o-old-2", "wave-a-old", OutreachStatus.COMPLETED, True),
    ]
    for record_id, campaign_id, status, crisis in records:
        session.add(
            OutreachRecordModel(
                id=record_id,
                tenant_id=TENANT,
                campaign_id=campaign_id,
                member_id="member-a" if campaign_id != "wave-b" else "member-b",
                counsellor_id=None,
                status=status,
                contact_attempts=0,
                crisis_flag=crisis,
                created_at=now,
                updated_at=now,
            )
        )
    await session.commit()


async def _seed_surveys(session, now: datetime) -> None:
    approved = [{"key": "helpful", "label": "Was the service helpful?", "choices": ["Yes", "No"]}]
    for campaign_id, client_id in (("survey-a", CLIENT_A), ("survey-b", CLIENT_B)):
        session.add(
            SurveyCampaignModel(
                id=campaign_id,
                tenant_id=TENANT,
                client_id=client_id,
                name=campaign_id,
                source="GoogleForms",
                external_form_id="form",
                webhook_secret="x" * 40,
                status=SurveyCampaignStatus.ACTIVE,
                anonymous=True,
                approved_questions=approved,
                response_count=0,
                created_by="user-1",
                created_at=now,
                updated_at=now,
            )
        )
    await session.commit()

    responses = [
        ("r-a-in-1", "survey-a", "2026-01-10T08:00:00", "Yes"),
        ("r-a-in-2", "survey-a", "2026-01-31T18:00:00", "No"),
        ("r-a-before", "survey-a", "2025-12-01T08:00:00", "Yes"),
        ("r-b-in", "survey-b", "2026-01-10T08:00:00", "Yes"),
    ]
    for response_id, campaign_id, when, answer in responses:
        session.add(
            SurveyResponseModel(
                id=response_id,
                tenant_id=TENANT,
                campaign_id=campaign_id,
                external_response_id=response_id,
                submitted_at=_at(when),
                received_at=now,
                payload={"helpful": answer, "comment": "Namulondo, 0772 000 111"},
                created_at=now,
                updated_at=now,
            )
        )
    await session.commit()


async def _run(db, query_type: ReportQueryType, **params):
    async with db() as session:
        runner = ReportQueryRunner(session, min_cell_size=1)
        return await runner.run(
            TemplateSection(title=query_type.value, query_type=query_type),
            tenant_id=TENANT,
            run_parameters=params,
        )


class TestSessionsByMonth:
    async def test_the_client_scope_is_applied(self, db):
        result = await _run(db, ReportQueryType.SESSIONS_BY_MONTH, client_id=CLIENT_A, **PERIOD)
        assert result["buckets"] == [{"month": "2026-01", "count": 3}]

    async def test_switching_the_client_changes_the_result(self, db):
        result = await _run(db, ReportQueryType.SESSIONS_BY_MONTH, client_id=CLIENT_B, **PERIOD)
        assert result["buckets"] == [{"month": "2026-01", "count": 1}]

    async def test_a_soft_deleted_session_is_excluded(self, db):
        """s-deleted sits inside the window and must not be counted."""
        result = await _run(db, ReportQueryType.SESSIONS_BY_MONTH, client_id=CLIENT_A, **PERIOD)
        assert result["total"] == 3

    async def test_the_last_day_is_inclusive_to_its_end(self, db):
        """The 15:00 record on 31 January is inside a window ending that day."""
        result = await _run(
            db,
            ReportQueryType.SESSIONS_BY_MONTH,
            client_id=CLIENT_A,
            **{"from": "2026-01-31", "to": "2026-01-31"},
        )
        assert result["total"] == 2

    async def test_the_window_is_read_in_the_report_timezone(self, db):
        """22:00 UTC on 31 January is 01:00 on 1 February in Kampala."""
        utc = await _run(
            db,
            ReportQueryType.SESSIONS_BY_MONTH,
            client_id=CLIENT_A,
            **{"from": "2026-01-31", "to": "2026-01-31"},
        )
        kampala = await _run(
            db,
            ReportQueryType.SESSIONS_BY_MONTH,
            client_id=CLIENT_A,
            timezone="Africa/Kampala",
            **{"from": "2026-01-31", "to": "2026-01-31"},
        )
        assert utc["total"] == 2
        assert kampala["total"] == 1

    async def test_the_scope_applied_is_reported(self, db):
        result = await _run(db, ReportQueryType.SESSIONS_BY_MONTH, client_id=CLIENT_A, **PERIOD)
        assert result["scope"]["client_id"] == CLIENT_A
        assert result["scope"]["from"] == "2026-01-01"
        assert result["scope"]["to"] == "2026-01-31"


class TestDiagnosisPrevalence:
    async def test_the_client_scope_is_applied(self, db):
        result = await _run(db, ReportQueryType.DIAGNOSIS_PREVALENCE, client_id=CLIENT_A, **PERIOD)
        assert [(b["code"], b["count"]) for b in result["buckets"]] == [("STRESS", 2)]

    async def test_another_client_diagnosis_does_not_leak(self, db):
        result = await _run(db, ReportQueryType.DIAGNOSIS_PREVALENCE, client_id=CLIENT_A, **PERIOD)
        assert "GRIEF" not in [b["code"] for b in result["buckets"]]

    async def test_unclassified_sessions_stay_in_the_same_scope(self, db):
        result = await _run(db, ReportQueryType.DIAGNOSIS_PREVALENCE, client_id=CLIENT_A, **PERIOD)
        assert result["unclassified_sessions"] == 1


class TestContractUtilisation:
    async def test_only_live_contracts_of_the_client_inside_the_period_count(self, db):
        result = await _run(db, ReportQueryType.CONTRACT_UTILISATION, client_id=CLIENT_A, **PERIOD)
        assert result["buckets"] == [
            {"contract_id": "contract-a", "total_units": 8, "event_count": 2}
        ]

    async def test_a_retired_contract_is_excluded_even_without_a_client_filter(self, db):
        result = await _run(db, ReportQueryType.CONTRACT_UTILISATION, **PERIOD)
        assert "contract-a-retired" not in [b["contract_id"] for b in result["buckets"]]


class TestCareCallbackOutcomes:
    async def test_the_period_selects_the_waves_that_opened_inside_it(self, db):
        result = await _run(
            db, ReportQueryType.CARE_CALLBACK_OUTCOMES, client_id=CLIENT_A, **PERIOD
        )
        assert result["total"] == 3
        assert result["crisis_flags"] == 1

    async def test_another_client_wave_is_excluded(self, db):
        result = await _run(
            db, ReportQueryType.CARE_CALLBACK_OUTCOMES, client_id=CLIENT_B, **PERIOD
        )
        assert result["total"] == 1

    async def test_a_client_filter_without_a_campaign_does_not_error(self, db):
        """The crisis-flag count used to fail to compile with a client join."""
        result = await _run(db, ReportQueryType.CARE_CALLBACK_OUTCOMES, client_id=CLIENT_A)
        assert result["crisis_flags"] == 3

    async def test_a_campaign_from_another_client_is_rejected(self, db):
        with pytest.raises(DomainError, match="campaign_id"):
            await _run(
                db,
                ReportQueryType.CARE_CALLBACK_OUTCOMES,
                client_id=CLIENT_A,
                campaign_id="wave-b",
            )


class TestSatisfactionDistribution:
    async def test_the_period_and_client_scope_are_applied(self, db):
        result = await _run(
            db, ReportQueryType.SATISFACTION_DISTRIBUTION, client_id=CLIENT_A, **PERIOD
        )
        assert result["response_total"] == 2
        assert result["answer_frequencies"]["helpful"] == {"Yes": 1, "No": 1}

    async def test_another_client_response_is_excluded(self, db):
        result = await _run(
            db, ReportQueryType.SATISFACTION_DISTRIBUTION, client_id=CLIENT_B, **PERIOD
        )
        assert result["response_total"] == 1

    async def test_free_text_never_reaches_the_report(self, db):
        result = await _run(
            db, ReportQueryType.SATISFACTION_DISTRIBUTION, client_id=CLIENT_A, **PERIOD
        )
        assert "Namulondo" not in str(result)
        assert "comment" not in result["answer_frequencies"]


class TestParameterHandling:
    async def test_an_unsupported_parameter_is_rejected(self, db):
        with pytest.raises(DomainError, match="Unsupported report parameter"):
            await _run(db, ReportQueryType.SESSIONS_BY_MONTH, clientId=CLIENT_A)

    async def test_a_parameter_a_section_cannot_use_is_named_in_the_scope(self, db):
        result = await _run(
            db, ReportQueryType.SESSIONS_BY_MONTH, client_id=CLIENT_A, campaign_id="wave-a"
        )
        assert result["scope"]["ignored_parameters"] == ["campaign_id"]
