"""The booking gate.

These cases were previously spread across ProviderProfile.is_panel_eligible and
the Person-based CheckProviderEligibilityUseCase, neither of which any
production write path called. They now run against the single policy that the
eligibility endpoint, session creation, rescheduling and outreach assignment
all use.
"""

from datetime import UTC, date, datetime, timedelta

import pytest

from app.domain.entities.provider import ProviderEntity
from app.domain.enums import (
    AccreditationStatus,
    BaseStatus,
    PanelStatus,
    ProviderTier,
    UgandaRegion,
)
from app.domain.services.provider_eligibility import (
    ProviderNotEligibleError,
    evaluate_practitioner,
    require_eligible,
)
from app.domain.services.provider_network_calendar import boundary_day
from app.domain.value_objects.core import ProviderId, ProviderProfile, TenantId
from app.shared.utils.datetime import utc_now

NOW = datetime(2026, 9, 6, 9, 0, tzinfo=UTC)
SOON = datetime(2026, 9, 20, 9, 0, tzinfo=UTC)


def _profile(
    *,
    panel: PanelStatus = PanelStatus.ACTIVE,
    accreditation: AccreditationStatus = AccreditationStatus.ACCREDITED,
    expiry: date | None = None,
) -> ProviderProfile:
    return ProviderProfile(
        tier=ProviderTier.T1,
        region=UgandaRegion.KAMPALA_METRO,
        accreditation_status=accreditation,
        panel_status=panel,
        accreditation_authority="UCC",
        accreditation_expiry=expiry,
        specialties=("MENTAL_ILL_HEALTH",),
    )


def _provider(
    profile: ProviderProfile | None = None,
    *,
    status: BaseStatus = BaseStatus.ACTIVE,
    deleted: bool = False,
) -> ProviderEntity:
    now = utc_now()
    return ProviderEntity(
        id=ProviderId("prov-1"),
        tenant_id=TenantId("t-1"),
        status=status,
        display_name="Amina Okello",
        created_at=now,
        updated_at=now,
        provider_profile=_profile() if profile is None else profile,
        deleted_at=now if deleted else None,
    )


def _codes(provider: ProviderEntity, *, scheduled_at=SOON, now=NOW) -> set[str]:
    return {
        r.code for r in evaluate_practitioner(provider, scheduled_at=scheduled_at, now=now).reasons
    }


class TestPractitionerGate:
    def test_eligible_when_active_accredited_and_unexpired(self):
        provider = _provider(_profile(expiry=date(2027, 1, 1)))
        assert evaluate_practitioner(provider, scheduled_at=SOON, now=NOW).eligible is True

    def test_ineligible_when_panel_suspended(self):
        assert _codes(_provider(_profile(panel=PanelStatus.SUSPENDED))) == {"panel_not_active"}

    def test_ineligible_when_panel_pending(self):
        assert _codes(_provider(_profile(panel=PanelStatus.PENDING))) == {"panel_not_active"}

    def test_ineligible_when_accreditation_lapsed(self):
        assert _codes(_provider(_profile(accreditation=AccreditationStatus.LAPSED))) == {
            "not_accredited"
        }

    def test_eligible_when_no_expiry_recorded(self):
        """No expiry means no recorded expiry, not a fabricated one."""
        assert (
            evaluate_practitioner(
                _provider(_profile(expiry=None)), scheduled_at=SOON, now=NOW
            ).eligible
            is True
        )

    def test_ineligible_when_record_not_active(self):
        assert _codes(_provider(status=BaseStatus.PENDING)) == {"provider_not_active"}

    def test_deleted_record_reports_only_that(self):
        assert _codes(_provider(deleted=True)) == {"provider_deleted"}

    def test_missing_profile_reported(self):
        provider = _provider()
        provider.provider_profile = None
        assert _codes(provider) == {"provider_no_profile"}

    def test_every_failing_rule_is_reported(self):
        provider = _provider(
            _profile(panel=PanelStatus.REMOVED, accreditation=AccreditationStatus.REJECTED),
            status=BaseStatus.INACTIVE,
        )
        assert _codes(provider) == {"provider_not_active", "panel_not_active", "not_accredited"}


class TestExpiryBoundary:
    def test_expiry_is_valid_through_that_day(self):
        """Decision 7 treats an expiry date as valid through that date."""
        service_day = boundary_day(SOON)
        provider = _provider(_profile(expiry=service_day))
        assert evaluate_practitioner(provider, scheduled_at=SOON, now=NOW).eligible is True

    def test_expiry_the_day_before_the_service_date_fails(self):
        service_day = boundary_day(SOON)
        provider = _provider(_profile(expiry=service_day - timedelta(days=1)))
        assert _codes(provider) == {"accreditation_expired"}

    def test_expiry_must_cover_today_as_well_as_the_service_date(self):
        """A past expiry blocks a future booking even though the record still reads Accredited."""
        provider = _provider(_profile(expiry=boundary_day(NOW) - timedelta(days=1)))
        assert _codes(provider) == {"accreditation_expired"}

    def test_the_day_is_taken_in_kampala_not_utc(self):
        """22:30Z on 30 June is already 1 July in Kampala, so a 30 June expiry has passed."""
        late_evening_utc = datetime(2026, 6, 30, 22, 30, tzinfo=UTC)
        assert boundary_day(late_evening_utc) == date(2026, 7, 1)
        provider = _provider(_profile(expiry=date(2026, 6, 30)))
        codes = _codes(provider, scheduled_at=late_evening_utc, now=late_evening_utc)
        assert codes == {"accreditation_expired"}

    def test_a_naive_datetime_is_rejected_rather_than_assumed(self):
        with pytest.raises(ValueError, match="aware datetime"):
            boundary_day(datetime(2026, 6, 30, 22, 30))


class TestRequireEligible:
    def test_raises_with_every_reason_code_in_the_body(self):
        provider = _provider(_profile(panel=PanelStatus.SUSPENDED))
        decision = evaluate_practitioner(provider, scheduled_at=SOON, now=NOW)
        with pytest.raises(ProviderNotEligibleError) as caught:
            require_eligible(decision, provider.id.value)
        body = caught.value.to_api_response()
        assert body["error"] == "PROVIDER_NOT_ELIGIBLE"
        assert caught.value.http_status == 409
        assert {d["code"] for d in body["details"]} == {"provider_id", "panel_not_active"}

    def test_passes_silently_when_eligible(self):
        decision = evaluate_practitioner(_provider(), scheduled_at=SOON, now=NOW)
        require_eligible(decision, "prov-1")
