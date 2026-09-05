"""Provider panel-status + tier audit tests on PersonEntity (Phase 4 #D-Provider)."""

from datetime import UTC, datetime

import pytest

from app.domain.entities.person import PersonEntity
from app.domain.entities.user import UserEntity
from app.domain.enums import (
    AccreditationStatus,
    BaseStatus,
    PanelStatus,
    ProviderTier,
    UgandaRegion,
    UserStatus,
)
from app.domain.events import (
    ProviderPanelStatusChanged,
    ProviderTierChanged,
)
from app.domain.exceptions import DomainError
from app.domain.value_objects.core import (
    Email,
    LicenseInfo,
    PersonId,
    ProviderProfile,
    TenantId,
    UserId,
)


def _user() -> UserEntity:
    now = datetime.now(UTC)
    return UserEntity(
        id=UserId("u-1"),
        tenant_id=TenantId("t-1"),
        email=Email("p@example.com"),
        status=UserStatus.ACTIVE,
        is_two_factor_enabled=False,
        created_at=now,
        updated_at=now,
    )


def _profile(
    tier: ProviderTier = ProviderTier.T2,
    panel_status: PanelStatus = PanelStatus.ACTIVE,
) -> ProviderProfile:
    return ProviderProfile(
        tier=tier,
        region=UgandaRegion.CENTRAL,
        accreditation_status=AccreditationStatus.ACCREDITED,
        panel_status=panel_status,
    )


def _provider(
    *,
    profile: ProviderProfile | None = None,
    status: BaseStatus = BaseStatus.ACTIVE,
) -> PersonEntity:
    person = PersonEntity.create_service_provider(
        id=PersonId("prov-1"),
        tenant_id=TenantId("t-1"),
        user_id=UserId("u-1"),
        profile=_user(),
        license_info=LicenseInfo(number="L-123", issuing_authority="UMC"),
    )
    person.update_provider_profile(profile or _profile())
    person.status = status
    return person


class TestPanelStatusChange:
    def test_emits_event_on_change(self):
        p = _provider()
        p.events.clear()
        p.change_panel_status(
            new_status=PanelStatus.SUSPENDED,
            actor=UserId("admin"),
            reason="Quality review pending",
        )
        assert p.provider_profile.panel_status == PanelStatus.SUSPENDED
        events = [e for e in p.events if isinstance(e, ProviderPanelStatusChanged)]
        assert len(events) == 1
        assert events[0].old_status == "Active"
        assert events[0].new_status == "Suspended"
        assert events[0].reason == "Quality review pending"

    def test_no_event_when_status_unchanged(self):
        p = _provider()
        p.events.clear()
        p.change_panel_status(
            new_status=PanelStatus.ACTIVE,
            actor=UserId("admin"),
            reason="re-confirm",
        )
        assert not [e for e in p.events if isinstance(e, ProviderPanelStatusChanged)]

    def test_reason_required(self):
        p = _provider()
        with pytest.raises(DomainError, match="reason"):
            p.change_panel_status(
                new_status=PanelStatus.SUSPENDED,
                actor=UserId("admin"),
                reason="",
            )

    def test_blocked_for_deleted_person(self):
        p = _provider(status=BaseStatus.DELETED)
        with pytest.raises(DomainError):
            p.change_panel_status(
                new_status=PanelStatus.SUSPENDED,
                actor=UserId("admin"),
                reason="x",
            )


class TestTierChange:
    def test_emits_event_on_change(self):
        p = _provider(profile=_profile(tier=ProviderTier.T2))
        p.events.clear()
        p.change_tier(
            new_tier=ProviderTier.T1,
            actor=UserId("admin"),
            reason="Promoted after annual review",
        )
        assert p.provider_profile.tier == ProviderTier.T1
        events = [e for e in p.events if isinstance(e, ProviderTierChanged)]
        assert len(events) == 1
        assert events[0].old_tier == "T2"
        assert events[0].new_tier == "T1"

    def test_idempotent_when_unchanged(self):
        p = _provider(profile=_profile(tier=ProviderTier.T2))
        p.events.clear()
        p.change_tier(
            new_tier=ProviderTier.T2,
            actor=UserId("admin"),
            reason="reaffirm",
        )
        assert not [e for e in p.events if isinstance(e, ProviderTierChanged)]

    def test_reason_required(self):
        p = _provider()
        with pytest.raises(DomainError, match="reason"):
            p.change_tier(
                new_tier=ProviderTier.T1,
                actor=UserId("admin"),
                reason="",
            )

    def test_provider_profile_required(self):
        person = PersonEntity.create_service_provider(
            id=PersonId("p-2"),
            tenant_id=TenantId("t-1"),
            user_id=UserId("u-1"),
            profile=_user(),
            license_info=LicenseInfo(number="L", issuing_authority="UMC"),
        )
        # provider_profile defaults to None until update_provider_profile is called
        assert person.provider_profile is None
        with pytest.raises(DomainError, match="no panel profile"):
            person.change_tier(
                new_tier=ProviderTier.T1,
                actor=UserId("admin"),
                reason="should fail",
            )
