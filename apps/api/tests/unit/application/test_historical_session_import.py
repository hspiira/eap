"""Historical acceptance is a different rule from new-booking eligibility.

A practitioner who cannot take new work today may still have delivered a
session in 2023. These pin that separation, and the limits that replace the
booking gate on this path.
"""

from datetime import UTC, datetime, timedelta
from types import SimpleNamespace

import pytest

from app.application.use_cases.historical_session_import import (
    HistoricalImportRejected,
    HistoricalSessionRecord,
    RecordHistoricalSessionUseCase,
)
from app.domain.entities.provider import ProviderEntity
from app.domain.enums import (
    AccreditationStatus,
    BaseStatus,
    PanelStatus,
    ProviderTier,
    SessionDeliveryContext,
    SessionStatus,
    UgandaRegion,
)
from app.domain.value_objects.core import (
    EligibleMemberId,
    ProviderId,
    ProviderProfile,
    ServiceId,
    SessionId,
    TenantId,
)
from app.shared.utils.datetime import utc_now

PAST = datetime(2023, 5, 17, 10, 0, tzinfo=UTC)


def _ineligible_provider(tenant: str = "t-1") -> ProviderEntity:
    """Removed from the panel and lapsed: no new booking would be accepted."""
    now = utc_now()
    return ProviderEntity(
        id=ProviderId("prov-1"),
        tenant_id=TenantId(tenant),
        status=BaseStatus.INACTIVE,
        display_name="Former Practitioner",
        created_at=now,
        updated_at=now,
        provider_profile=ProviderProfile(
            tier=ProviderTier.T3,
            region=UgandaRegion.NORTHERN,
            accreditation_status=AccreditationStatus.LAPSED,
            panel_status=PanelStatus.REMOVED,
        ),
    )


class _Sessions:
    def __init__(self):
        self.saved = []

    async def save(self, session):
        self.saved.append(session)


class _Providers:
    def __init__(self, provider=None):
        self.provider = provider

    async def get_by_id(self, provider_id):
        return self.provider


def _record(**overrides) -> HistoricalSessionRecord:
    base = dict(
        session_id=SessionId("s-1"),
        tenant_id=TenantId("t-1"),
        service_id=ServiceId("svc-1"),
        provider_id=ProviderId("prov-1"),
        member_id=EligibleMemberId("m-1"),
        delivered_at=PAST,
        delivery_context=SessionDeliveryContext.UNKNOWN,
    )
    base.update(overrides)
    return HistoricalSessionRecord(**base)


_DEFAULT = object()


async def _run(record, provider=_DEFAULT):
    """Run the use case. Pass provider=None to mean the practitioner is missing."""
    resolved = _ineligible_provider() if provider is _DEFAULT else provider
    sessions = _Sessions()
    use_case = RecordHistoricalSessionUseCase(sessions, _Providers(resolved))
    result = await use_case.execute(record)
    return result, sessions


class TestHistoricalAcceptance:
    async def test_accepts_a_practitioner_who_is_ineligible_today(self):
        """The point of the separate path: past delivery is not present eligibility."""
        session, sessions = await _run(_record())
        assert session.status is SessionStatus.COMPLETED
        assert session.scheduled_at == PAST
        assert session.completed_at == PAST
        assert len(sessions.saved) == 1

    async def test_unknown_context_is_accepted_here_and_nowhere_else(self):
        session, _ = await _run(_record(delivery_context=SessionDeliveryContext.UNKNOWN))
        assert session.delivery_context is SessionDeliveryContext.UNKNOWN
        assert session.provider_affiliation_id is None

    async def test_organisation_delivery_keeps_its_affiliation(self):
        session, _ = await _run(
            _record(
                delivery_context=SessionDeliveryContext.ORGANISATION,
                provider_affiliation_id="aff-1",
            )
        )
        assert session.provider_affiliation_id == "aff-1"


class TestHistoricalRejections:
    async def test_refuses_a_future_session(self):
        """The import path cannot be used to book, which would skip the gate."""
        future = utc_now() + timedelta(days=30)
        with pytest.raises(HistoricalImportRejected) as caught:
            await _run(_record(delivered_at=future))
        assert caught.value.error_code == "future_session_through_import"

    async def test_refuses_a_practitioner_from_another_tenant(self):
        with pytest.raises(HistoricalImportRejected) as caught:
            await _run(_record(), provider=_ineligible_provider(tenant="t-other"))
        assert caught.value.error_code == "practitioner_not_in_tenant"

    async def test_refuses_an_unresolved_practitioner(self):
        """Never invent a person; an unresolved row stays staged."""
        with pytest.raises(HistoricalImportRejected) as caught:
            await _run(_record(), provider=None)
        assert caught.value.error_code == "practitioner_not_in_tenant"

    async def test_refuses_organisation_delivery_without_an_affiliation(self):
        with pytest.raises(HistoricalImportRejected) as caught:
            await _run(_record(delivery_context=SessionDeliveryContext.ORGANISATION))
        assert caught.value.error_code == "delivery_context_inconsistent"

    async def test_refuses_unknown_delivery_carrying_an_affiliation(self):
        with pytest.raises(HistoricalImportRejected) as caught:
            await _run(_record(provider_affiliation_id="aff-1"))
        assert caught.value.error_code == "delivery_context_inconsistent"


class TestNoLiveSideEffects:
    async def test_records_without_touching_billing_or_authorization(self):
        """The use case takes no authorization or billing collaborator at all."""
        import inspect

        signature = inspect.signature(RecordHistoricalSessionUseCase.__init__)
        assert set(signature.parameters) == {"self", "session_repository", "provider_repository"}

    async def test_emits_no_completion_event(self):
        session, _ = await _run(_record())
        assert [type(e).__name__ for e in session.events] == []


def test_the_module_does_not_import_the_booking_gate():
    """Historical acceptance must not be able to consult present eligibility."""
    import app.application.use_cases.historical_session_import as module

    source = SimpleNamespace(text=open(module.__file__).read())
    assert "evaluate_practitioner" not in source.text
    assert "require_eligible" not in source.text
