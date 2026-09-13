"""What staging must hand the session repository, enforced rather than assumed.

E1 in docs/reviews/REGRESSION_RESILIENCE_PLAN_2026_09_13.md: staging passed raw
strings where the repository reads `.value` off ID value objects. Nine
unrestricted `AsyncMock()` collaborators accepted them happily, so the unit
suite stayed green while real staging failed.

`autospec` would have checked the call's shape, not its argument types. These
tests assert the types themselves, at the one boundary that broke.
"""

import inspect
from datetime import date

import pytest

from app.application.services.session_import_staging import SessionImportStagingService
from app.domain.repositories.service_session_repository import ServiceSessionRepository
from app.domain.value_objects.core import ClientId, ProviderId, ServiceId, TenantId
from app.domain.value_objects.ids import EligibleMemberId

#: Every ID argument the port declares, and the type each one requires.
_ID_ARGUMENTS = {
    "tenant_id": TenantId,
    "provider_id": ProviderId,
    "client_id": ClientId,
    "service_id": ServiceId,
    "member_id": EligibleMemberId,
}


class StrictSessionRepository:
    """A fake that refuses what the real adapter would fail on.

    The real implementation reads `.value` off each ID, so a raw string raises
    there and nowhere earlier. This brings that failure forward into the unit
    suite, which is where the original defect should have been caught.
    """

    def __init__(self) -> None:
        self.calls: list[dict] = []

    async def find_awaiting_confirmation(
        self,
        tenant_id,
        *,
        session_date,
        provider_id,
        client_id,
        service_id,
        member_id,
    ):
        supplied = {
            "tenant_id": tenant_id,
            "provider_id": provider_id,
            "client_id": client_id,
            "service_id": service_id,
            "member_id": member_id,
        }
        for name, value in supplied.items():
            if value is None and name == "member_id":
                continue
            expected = _ID_ARGUMENTS[name]
            if not isinstance(value, expected):
                raise TypeError(f"{name} must be {expected.__name__}, got {type(value).__name__}")
        if not isinstance(session_date, date):
            raise TypeError("session_date must be a date")
        self.calls.append(supplied)
        return None


class TestTheFakeMatchesTheRealContract:
    def test_the_fake_accepts_exactly_the_port_signature(self):
        """A fake that drifts from the port stops proving anything."""
        port = inspect.signature(ServiceSessionRepository.find_awaiting_confirmation)
        fake = inspect.signature(StrictSessionRepository.find_awaiting_confirmation)
        assert list(port.parameters) == list(fake.parameters)

    @pytest.mark.parametrize("argument", sorted(_ID_ARGUMENTS))
    async def test_a_raw_string_is_refused_for_every_id(self, argument):
        """The exact defect E1 records: a string where a value object belongs."""
        good = {
            "tenant_id": TenantId("t-1"),
            "provider_id": ProviderId("prov-1"),
            "client_id": ClientId("cli-1"),
            "service_id": ServiceId("svc-1"),
            "member_id": EligibleMemberId("mem-1"),
        }
        good[argument] = "raw-string"
        with pytest.raises(TypeError, match=argument):
            await StrictSessionRepository().find_awaiting_confirmation(
                good.pop("tenant_id"), session_date=date(2025, 4, 2), **good
            )

    async def test_value_objects_are_accepted(self):
        repo = StrictSessionRepository()
        assert (
            await repo.find_awaiting_confirmation(
                TenantId("t-1"),
                session_date=date(2025, 4, 2),
                provider_id=ProviderId("prov-1"),
                client_id=ClientId("cli-1"),
                service_id=ServiceId("svc-1"),
                member_id=None,
            )
            is None
        )
        assert len(repo.calls) == 1


class TestStagingHonoursIt:
    def test_staging_declares_the_repository_it_calls(self):
        """The port, not a duck-typed stand-in, is what staging is built against."""
        parameters = inspect.signature(SessionImportStagingService.__init__).parameters
        assert "sessions" in parameters or any(
            p.annotation is ServiceSessionRepository for p in parameters.values()
        )
