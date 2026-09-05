"""Selecting and consuming the authorization a completed session draws down."""

from datetime import date, timedelta

import pytest

from app.application.use_cases.authorization_drawdown import (
    ConsumeAuthorizationForSessionUseCase,
    select_authorization,
)
from app.domain.entities.authorization import Authorization
from app.domain.enums import AuthorizationStatus, ServiceCategory
from app.domain.value_objects.core import (
    AuthorizationId,
    CaseId,
    ClinicalSubjectId,
    EAPProgrammeId,
    TenantId,
)
from app.shared.utils.datetime import utc_now

TENANT = TenantId("t_1")
CASE = CaseId("case_1")
COUNSELLING = ServiceCategory.SHORT_TERM_COUNSELLING
CRISIS = ServiceCategory.CRISIS_INTERVENTION


def _auth(
    ident="a1",
    *,
    category=COUNSELLING,
    granted=6,
    used=0,
    status=AuthorizationStatus.ACTIVE,
    expires_on=None,
    granted_days_ago=0,
):
    now = utc_now()
    return Authorization(
        id=AuthorizationId(ident),
        tenant_id=TENANT,
        case_id=CASE,
        clinical_subject_id=ClinicalSubjectId("cs_1"),
        programme_id=EAPProgrammeId("p_1"),
        service_category=category,
        sessions_granted=granted,
        sessions_used=used,
        status=status,
        granted_at=now - timedelta(days=granted_days_ago),
        created_at=now,
        updated_at=now,
        expires_on=expires_on,
    )


class FakeAuthorizationRepository:
    def __init__(self, rows):
        self.rows = rows
        self.saved = []

    async def list_for_case(self, tenant_id, case_id):
        return list(self.rows)

    async def save(self, entity):
        self.saved.append(entity)


class TestSelection:
    def test_no_authorizations_selects_nothing(self):
        assert select_authorization([], service_category=COUNSELLING) is None

    def test_a_different_category_is_not_selected(self):
        assert select_authorization([_auth(category=CRISIS)], service_category=COUNSELLING) is None

    def test_an_exhausted_authorization_is_not_selected(self):
        rows = [_auth(granted=4, used=4)]
        assert select_authorization(rows, service_category=COUNSELLING) is None

    def test_an_expired_authorization_is_not_selected(self):
        rows = [_auth(expires_on=date.today() - timedelta(days=1))]
        assert select_authorization(rows, service_category=COUNSELLING) is None

    def test_a_closed_authorization_is_not_selected(self):
        rows = [_auth(status=AuthorizationStatus.CLOSED)]
        assert select_authorization(rows, service_category=COUNSELLING) is None

    def test_the_nearest_to_exhaustion_is_spent_first(self):
        plenty = _auth("plenty", granted=10, used=0)
        nearly = _auth("nearly", granted=10, used=9)
        chosen = select_authorization([plenty, nearly], service_category=COUNSELLING)
        assert chosen.id.value == "nearly"

    def test_an_older_grant_breaks_a_tie(self):
        newer = _auth("newer", granted=5, used=1, granted_days_ago=1)
        older = _auth("older", granted=5, used=1, granted_days_ago=30)
        chosen = select_authorization([newer, older], service_category=COUNSELLING)
        assert chosen.id.value == "older"


class TestConsumption:
    async def _run(self, rows, category=COUNSELLING):
        repo = FakeAuthorizationRepository(rows)
        result = await ConsumeAuthorizationForSessionUseCase(repo).execute(
            tenant_id=TENANT, case_id=CASE, service_category=category
        )
        return result, repo

    @pytest.mark.asyncio
    async def test_a_matching_authorization_is_consumed_and_saved(self):
        auth = _auth(granted=6, used=2)
        result, repo = await self._run([auth])
        assert result.consumed
        assert auth.sessions_used == 3
        assert repo.saved == [auth]

    @pytest.mark.asyncio
    async def test_an_untyped_service_draws_down_nothing(self):
        result, repo = await self._run([_auth()], category=None)
        assert not result.consumed
        assert "no category" in result.reason.lower()
        assert repo.saved == []

    @pytest.mark.asyncio
    async def test_no_match_reports_why_and_saves_nothing(self):
        result, repo = await self._run([_auth(category=CRISIS)])
        assert not result.consumed
        assert "ShortTermCounselling" in result.reason
        assert repo.saved == []

    @pytest.mark.asyncio
    async def test_consuming_the_last_session_exhausts_the_authorization(self):
        auth = _auth(granted=3, used=2)
        result, _ = await self._run([auth])
        assert result.consumed
        assert auth.status is AuthorizationStatus.EXHAUSTED
        assert auth.sessions_remaining == 0

    @pytest.mark.asyncio
    async def test_an_exhausted_case_is_reported_not_raised(self):
        result, repo = await self._run([_auth(granted=2, used=2)])
        assert not result.consumed
        assert result.reason
        assert repo.saved == []
