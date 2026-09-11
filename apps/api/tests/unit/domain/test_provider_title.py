"""A practitioner's title is held apart from their name and composed for display."""

from dataclasses import replace

import pytest

from app.domain.entities.provider import ProviderEntity
from app.domain.enums import (
    AccreditationStatus,
    BaseStatus,
    PanelStatus,
    ProviderTier,
    ProviderTitle,
    UgandaRegion,
)
from app.domain.services.provider_alias_normalisation import normalise_practitioner_name
from app.domain.value_objects.core import ProviderId, ProviderProfile, TenantId, UserId
from app.shared.utils.datetime import utc_now

ADMIN = UserId("admin")


def _provider(title: ProviderTitle | None = None) -> ProviderEntity:
    now = utc_now()
    provider = ProviderEntity(
        id=ProviderId("prov-1"),
        tenant_id=TenantId("t-1"),
        status=BaseStatus.ACTIVE,
        display_name="Amina Okello",
        created_at=now,
        updated_at=now,
        provider_profile=ProviderProfile(
            tier=ProviderTier.T2,
            region=UgandaRegion.CENTRAL,
            accreditation_status=AccreditationStatus.ACCREDITED,
            panel_status=PanelStatus.ACTIVE,
            title=title,
        ),
    )
    provider.clear_events()
    return provider


class TestWrittenForm:
    @pytest.mark.parametrize(
        "title,expected",
        [
            (ProviderTitle.DR, "Dr."),
            (ProviderTitle.PROF, "Prof."),
            (ProviderTitle.MS, "Ms."),
            (ProviderTitle.MISS, "Miss"),
        ],
    )
    def test_a_shortened_title_takes_a_stop_and_a_whole_word_does_not(self, title, expected):
        assert title.written == expected


class TestFormalName:
    def test_the_title_is_composed_onto_the_name(self):
        assert _provider(ProviderTitle.DR).formal_name == "Dr. Amina Okello"

    def test_a_practitioner_without_one_is_just_their_name(self):
        assert _provider().formal_name == "Amina Okello"

    def test_the_stored_name_never_carries_the_title(self):
        """The name is the name; the title is composed on top of it."""
        provider = _provider(ProviderTitle.DR)
        assert provider.display_name == "Amina Okello"


class TestMatching:
    def test_an_extract_writing_the_title_still_matches_the_stored_name(self):
        """Why the title is stored apart: the normaliser strips it either way."""
        assert normalise_practitioner_name("DR. AMINA OKELLO") == normalise_practitioner_name(
            _provider(ProviderTitle.DR).display_name
        )

    def test_every_title_this_system_stores_is_one_the_normaliser_strips(self):
        """A title the normaliser kept would never match its own practitioner."""
        for title in ProviderTitle:
            assert normalise_practitioner_name(f"{title.written} Amina Okello") == "amina okello"


class TestUpdating:
    def test_a_title_can_be_set_through_the_audited_profile_path(self):
        provider = _provider()
        changed = provider.apply_profile_changes(ADMIN, title=ProviderTitle.PROF)
        assert changed == ("title",)
        assert provider.formal_name == "Prof. Amina Okello"

    def test_a_title_can_be_cleared(self):
        provider = _provider(ProviderTitle.DR)
        provider.apply_profile_changes(ADMIN, title=None)
        assert provider.formal_name == "Amina Okello"

    def test_omitting_it_leaves_the_title_alone(self):
        provider = _provider(ProviderTitle.DR)
        provider.apply_profile_changes(ADMIN, bio="Trauma-informed")
        assert provider.provider_profile.title is ProviderTitle.DR

    def test_setting_the_same_title_is_not_a_change(self):
        provider = _provider(ProviderTitle.DR)
        assert provider.apply_profile_changes(ADMIN, title=ProviderTitle.DR) == ()


class TestPersistence:
    def test_the_title_survives_a_profile_round_trip(self):
        from app.infrastructure.mappers.provider_mapper import ProviderMapper

        profile = replace(_provider(ProviderTitle.REV).provider_profile)
        stored = ProviderMapper.profile_to_dict(profile)
        assert stored["title"] == "Rev"
        assert ProviderMapper.profile_from_dict(stored).title is ProviderTitle.REV

    def test_a_profile_stored_before_titles_existed_reads_as_none(self):
        from app.infrastructure.mappers.provider_mapper import ProviderMapper

        legacy = {"tier": "T2", "region": "Central", "accreditation_status": "Accredited"}
        assert ProviderMapper.profile_from_dict(legacy).title is None
