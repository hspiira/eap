"""ProviderProfile + non-compete tests (Phase 2 #D-Provider)."""

from datetime import UTC, date, datetime, timedelta

import pytest

from app.domain.entities.non_compete_clause import NonCompeteClauseEntity
from app.domain.enums import (
    AccreditationStatus,
    NonCompeteStatus,
    PanelStatus,
    ProviderTier,
    UgandaRegion,
)
from app.domain.exceptions import DomainError
from app.domain.value_objects.core import (
    NonCompeteClauseId,
    ProviderId,
    ProviderProfile,
    TenantId,
    UserId,
)
from app.shared.utils.datetime import utc_now


def _profile(
    *,
    tier: ProviderTier = ProviderTier.T1,
    region: UgandaRegion = UgandaRegion.KAMPALA_METRO,
    accreditation: AccreditationStatus = AccreditationStatus.ACCREDITED,
    panel: PanelStatus = PanelStatus.ACTIVE,
    expiry: date | None = None,
) -> ProviderProfile:
    return ProviderProfile(
        tier=tier,
        region=region,
        accreditation_status=accreditation,
        panel_status=panel,
        accreditation_authority="UCC",
        accreditation_expiry=expiry,
        specialties=("MENTAL_ILL_HEALTH",),
    )


class TestProviderProfile:
    def test_panel_eligible_with_active_accredited_unexpired(self):
        profile = _profile(expiry=utc_now().date() + timedelta(days=30))
        assert profile.is_panel_eligible() is True

    def test_panel_ineligible_when_panel_suspended(self):
        profile = _profile(panel=PanelStatus.SUSPENDED)
        assert profile.is_panel_eligible() is False

    def test_panel_ineligible_when_accreditation_lapsed(self):
        profile = _profile(accreditation=AccreditationStatus.LAPSED)
        assert profile.is_panel_eligible() is False

    def test_panel_ineligible_when_accreditation_expired(self):
        profile = _profile(expiry=utc_now().date() - timedelta(days=1))
        assert profile.is_panel_eligible() is False

    def test_panel_eligible_when_no_expiry(self):
        profile = _profile(expiry=None)
        assert profile.is_panel_eligible() is True


def _clause(
    *,
    status: NonCompeteStatus = NonCompeteStatus.DRAFT,
    effective_from: date | None = None,
    effective_until: date | None = None,
) -> NonCompeteClauseEntity:
    now = datetime.now(UTC)
    return NonCompeteClauseEntity(
        id=NonCompeteClauseId("nc-1"),
        tenant_id=TenantId("t-1"),
        provider_id=ProviderId("p-1"),
        status=status,
        terms_summary="No direct work with Minet clients for 12 months.",
        effective_from=effective_from or utc_now().date(),
        effective_until=effective_until,
        created_at=now,
        updated_at=now,
    )


class TestNonCompete:
    def test_sign_advances_status_and_records_signer(self):
        clause = _clause()
        clause.sign(UserId("usr-legal"))
        assert clause.status == NonCompeteStatus.ACTIVE
        assert clause.signed_by == UserId("usr-legal")
        assert clause.signed_at is not None

    def test_cannot_sign_active_clause(self):
        clause = _clause(status=NonCompeteStatus.ACTIVE)
        with pytest.raises(DomainError):
            clause.sign(UserId("usr-legal"))

    def test_revoke_requires_reason(self):
        clause = _clause(status=NonCompeteStatus.ACTIVE)
        with pytest.raises(DomainError):
            clause.revoke("")

    def test_revoke_marks_status_and_records_reason(self):
        clause = _clause(status=NonCompeteStatus.ACTIVE)
        clause.revoke("Provider transitioning roles")
        assert clause.status == NonCompeteStatus.REVOKED
        assert clause.revoked_reason == "Provider transitioning roles"

    def test_cannot_revoke_already_revoked(self):
        clause = _clause(status=NonCompeteStatus.REVOKED)
        with pytest.raises(DomainError):
            clause.revoke("again")

    def test_mark_expired_when_due(self):
        clause = _clause(
            status=NonCompeteStatus.ACTIVE,
            effective_from=utc_now().date() - timedelta(days=365),
            effective_until=utc_now().date() - timedelta(days=1),
        )
        clause.mark_expired_if_due()
        assert clause.status == NonCompeteStatus.EXPIRED

    def test_mark_expired_no_op_for_indefinite(self):
        clause = _clause(status=NonCompeteStatus.ACTIVE)
        clause.mark_expired_if_due()
        assert clause.status == NonCompeteStatus.ACTIVE

    def test_is_currently_binding_true_when_active_in_window(self):
        clause = _clause(
            status=NonCompeteStatus.ACTIVE,
            effective_until=utc_now().date() + timedelta(days=30),
        )
        assert clause.is_currently_binding() is True

    def test_is_currently_binding_false_when_revoked(self):
        clause = _clause(status=NonCompeteStatus.REVOKED)
        assert clause.is_currently_binding() is False

    def test_invalid_window_rejected(self):
        now = datetime.now(UTC)
        with pytest.raises(DomainError):
            NonCompeteClauseEntity(
                id=NonCompeteClauseId("nc-x"),
                tenant_id=TenantId("t-1"),
                provider_id=ProviderId("p-1"),
                status=NonCompeteStatus.DRAFT,
                terms_summary="x",
                effective_from=date(2026, 6, 1),
                effective_until=date(2026, 1, 1),
                created_at=now,
                updated_at=now,
            )
