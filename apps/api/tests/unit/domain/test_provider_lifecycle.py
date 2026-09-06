"""Practitioner lifecycle commands on the aggregate the routes actually use.

The panel-status and tier cases here were ported from the PersonEntity tests
that ran against a path no production route called. Accreditation, activation
and account linking are new commands.
"""

from datetime import date

import pytest

from app.domain.entities.provider import UNSET, ProviderEntity
from app.domain.enums import (
    AccreditationStatus,
    BaseStatus,
    PanelStatus,
    ProviderTier,
    UgandaRegion,
)
from app.domain.events import (
    ProviderAccountLinked,
    ProviderAccountUnlinked,
    ProviderAccreditationChanged,
    ProviderCreated,
    ProviderPanelStatusChanged,
    ProviderProfileUpdated,
    ProviderStatusChanged,
    ProviderTierChanged,
)
from app.domain.exceptions import ConflictError, DomainError
from app.domain.value_objects.core import ProviderId, ProviderProfile, TenantId, UserId
from app.shared.utils.datetime import utc_now

ADMIN = UserId("admin")


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
    user_id: UserId | None = None,
) -> ProviderEntity:
    now = utc_now()
    provider = ProviderEntity(
        id=ProviderId("prov-1"),
        tenant_id=TenantId("t-1"),
        status=status,
        display_name="Amina Okello",
        contact_email="amina@example.com",
        user_id=user_id,
        created_at=now,
        updated_at=now,
        provider_profile=profile or _profile(),
    )
    provider.clear_events()
    return provider


def _events(provider: ProviderEntity, kind: type) -> list:
    return [e for e in provider.events if isinstance(e, kind)]


class TestPanelStatusChange:
    def test_emits_event_on_change(self):
        provider = _provider()
        provider.change_panel_status(PanelStatus.SUSPENDED, ADMIN, "Quality review pending")
        assert provider.provider_profile.panel_status == PanelStatus.SUSPENDED
        events = _events(provider, ProviderPanelStatusChanged)
        assert len(events) == 1
        assert (events[0].old_status, events[0].new_status) == ("Active", "Suspended")
        assert events[0].reason == "Quality review pending"

    def test_no_event_when_status_unchanged(self):
        provider = _provider()
        provider.change_panel_status(PanelStatus.ACTIVE, ADMIN, "re-confirm")
        assert _events(provider, ProviderPanelStatusChanged) == []

    def test_reason_required(self):
        with pytest.raises(DomainError, match="reason"):
            _provider().change_panel_status(PanelStatus.SUSPENDED, ADMIN, "   ")

    def test_blocked_for_deleted_record(self):
        with pytest.raises(DomainError, match="deleted"):
            _provider(status=BaseStatus.DELETED).change_panel_status(
                PanelStatus.SUSPENDED, ADMIN, "x"
            )


class TestTierChange:
    def test_emits_event_on_change(self):
        provider = _provider(profile=_profile(tier=ProviderTier.T2))
        provider.change_tier(ProviderTier.T1, ADMIN, "Promoted after annual review")
        assert provider.provider_profile.tier == ProviderTier.T1
        events = _events(provider, ProviderTierChanged)
        assert len(events) == 1
        assert (events[0].old_tier, events[0].new_tier) == ("T2", "T1")

    def test_repeating_an_unchanged_command_is_a_no_op(self):
        provider = _provider(profile=_profile(tier=ProviderTier.T2))
        provider.change_tier(ProviderTier.T2, ADMIN, "reaffirm")
        assert _events(provider, ProviderTierChanged) == []

    def test_reason_required(self):
        with pytest.raises(DomainError, match="reason"):
            _provider().change_tier(ProviderTier.T1, ADMIN, "")

    def test_provider_profile_required(self):
        provider = _provider()
        provider.provider_profile = None
        with pytest.raises(DomainError, match="no panel profile"):
            provider.change_tier(ProviderTier.T1, ADMIN, "should fail")


class TestAccreditationChange:
    def test_status_authority_and_expiry_move_as_one_command(self):
        provider = _provider()
        provider.change_accreditation(
            ADMIN,
            "Certificate renewed",
            accreditation_status=AccreditationStatus.ACCREDITED,
            accreditation_authority="UCC",
            accreditation_expiry=date(2027, 6, 30),
        )
        profile = provider.provider_profile
        assert profile.accreditation_authority == "UCC"
        assert profile.accreditation_expiry == date(2027, 6, 30)
        event = _events(provider, ProviderAccreditationChanged)[0]
        assert event.new_expiry == "2027-06-30"
        assert event.old_expiry is None

    def test_omitted_expiry_is_left_alone(self):
        provider = _provider()
        provider.change_accreditation(
            ADMIN,
            "Suspended pending review",
            accreditation_status=AccreditationStatus.ACCREDITED,
            accreditation_expiry=date(2027, 6, 30),
        )
        provider.change_accreditation(
            ADMIN,
            "Lapsed",
            accreditation_status=AccreditationStatus.LAPSED,
        )
        assert provider.provider_profile.accreditation_expiry == date(2027, 6, 30)

    def test_explicit_none_clears_the_expiry(self):
        provider = _provider()
        provider.change_accreditation(
            ADMIN,
            "Set",
            accreditation_status=AccreditationStatus.ACCREDITED,
            accreditation_expiry=date(2027, 6, 30),
        )
        provider.change_accreditation(
            ADMIN,
            "Certificate withdrawn, no expiry on record",
            accreditation_status=AccreditationStatus.LAPSED,
            accreditation_expiry=None,
        )
        assert provider.provider_profile.accreditation_expiry is None

    def test_unchanged_command_is_a_no_op(self):
        provider = _provider()
        provider.change_accreditation(
            ADMIN, "reaffirm", accreditation_status=AccreditationStatus.ACCREDITED
        )
        assert _events(provider, ProviderAccreditationChanged) == []

    def test_reason_required(self):
        with pytest.raises(DomainError, match="reason"):
            _provider().change_accreditation(
                ADMIN, "", accreditation_status=AccreditationStatus.LAPSED
            )


class TestStatusChange:
    def test_activation_is_audited(self):
        provider = _provider(status=BaseStatus.PENDING)
        provider.change_status(BaseStatus.ACTIVE, ADMIN, "Checks complete")
        assert provider.status == BaseStatus.ACTIVE
        event = _events(provider, ProviderStatusChanged)[0]
        assert (event.old_status, event.new_status) == ("Pending", "Active")

    def test_unchanged_command_is_a_no_op(self):
        provider = _provider(status=BaseStatus.ACTIVE)
        provider.change_status(BaseStatus.ACTIVE, ADMIN, "reaffirm")
        assert _events(provider, ProviderStatusChanged) == []

    def test_reason_required(self):
        with pytest.raises(DomainError, match="reason"):
            _provider().change_status(BaseStatus.INACTIVE, ADMIN, " ")


class TestProfileUpdate:
    def test_partial_update_leaves_omitted_fields_alone(self):
        provider = _provider()
        changed = provider.apply_profile_changes(ADMIN, region=UgandaRegion.EASTERN)
        assert changed == ("region",)
        assert provider.provider_profile.region == UgandaRegion.EASTERN
        assert provider.display_name == "Amina Okello"
        assert provider.contact_email == "amina@example.com"

    def test_explicit_none_clears_a_nullable_field(self):
        provider = _provider()
        provider.apply_profile_changes(ADMIN, contact_email=None)
        assert provider.contact_email is None

    def test_no_change_emits_no_event(self):
        provider = _provider()
        assert provider.apply_profile_changes(ADMIN, display_name="Amina Okello") == ()
        assert _events(provider, ProviderProfileUpdated) == []

    def test_blank_display_name_rejected(self):
        with pytest.raises(DomainError, match="display name"):
            _provider().apply_profile_changes(ADMIN, display_name="   ")

    def test_reports_every_changed_field_in_one_event(self):
        provider = _provider()
        provider.apply_profile_changes(
            ADMIN, display_name="Amina N. Okello", contact_phone="+256700000000", bio="Counsellor"
        )
        event = _events(provider, ProviderProfileUpdated)[0]
        assert set(event.changed_fields) == {"display_name", "contact_phone", "bio"}

    def test_lifecycle_fields_are_not_reachable(self):
        """The command takes no tier, panel, accreditation or status keyword."""
        with pytest.raises(TypeError):
            _provider().apply_profile_changes(ADMIN, tier=ProviderTier.T1)

    def test_specialties_are_not_reachable(self):
        """Decision 5 makes the catalogue link the only way to record one."""
        with pytest.raises(TypeError):
            _provider().apply_profile_changes(ADMIN, specialties=("Trauma",))

    def test_unset_is_not_a_value(self):
        provider = _provider()
        assert provider.apply_profile_changes(ADMIN, contact_phone=UNSET) == ()
        assert provider.contact_phone is None


class TestAccountLink:
    def test_linking_records_the_account(self):
        provider = _provider()
        provider.link_account(UserId("u-9"), ADMIN, "Onboarding")
        assert provider.user_id == UserId("u-9")
        assert _events(provider, ProviderAccountLinked)[0].user_id == UserId("u-9")

    def test_linking_a_second_account_conflicts(self):
        provider = _provider(user_id=UserId("u-1"))
        with pytest.raises(ConflictError):
            provider.link_account(UserId("u-9"), ADMIN, "Onboarding")

    def test_relinking_the_same_account_is_a_no_op(self):
        provider = _provider(user_id=UserId("u-1"))
        provider.link_account(UserId("u-1"), ADMIN, "again")
        assert _events(provider, ProviderAccountLinked) == []

    def test_unlinking_keeps_the_practitioner(self):
        provider = _provider(user_id=UserId("u-1"))
        provider.unlink_account(ADMIN, "Left the organisation")
        assert provider.user_id is None
        assert provider.display_name == "Amina Okello"
        assert provider.status == BaseStatus.ACTIVE
        assert _events(provider, ProviderAccountUnlinked)[0].user_id == UserId("u-1")

    def test_unlinking_when_absent_is_a_no_op(self):
        provider = _provider()
        provider.unlink_account(ADMIN, "nothing to do")
        assert _events(provider, ProviderAccountUnlinked) == []

    def test_reason_required_both_ways(self):
        with pytest.raises(DomainError, match="reason"):
            _provider().link_account(UserId("u-9"), ADMIN, "")
        with pytest.raises(DomainError, match="reason"):
            _provider(user_id=UserId("u-1")).unlink_account(ADMIN, "")


def test_creation_emits_an_event():
    provider = _provider()
    provider.record_created(ADMIN)
    assert len(_events(provider, ProviderCreated)) == 1
