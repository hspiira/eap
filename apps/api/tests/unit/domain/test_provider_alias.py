"""Alias reconciliation keeps missing, unmapped and ambiguous separate (decision 5)."""

from datetime import UTC, datetime

import pytest

from app.domain.entities.provider_alias import ProviderAliasEntity
from app.domain.enums.provider_network import AliasResolutionState
from app.domain.exceptions import DomainError
from app.domain.services.provider_alias_normalisation import (
    is_usable_name,
    normalise_practitioner_name,
)
from app.domain.value_objects.core import ProviderId, TenantId, UserId
from app.domain.value_objects.provider_network import ProviderAliasId

AT = datetime(2026, 9, 6, 12, 0, tzinfo=UTC)
ACTOR = UserId("u-1")


def _alias(**overrides) -> ProviderAliasEntity:
    defaults = {
        "id": ProviderAliasId("al-1"),
        "tenant_id": TenantId("t-1"),
        "source_system": "sessions-csv",
        "source_value": "Dr Alice  Nakato",
        "normalized_value": "alice nakato",
        "created_at": AT,
        "updated_at": AT,
    }
    return ProviderAliasEntity(**{**defaults, **overrides})


class TestNormalisation:
    def test_titles_and_spacing_collapse(self):
        assert normalise_practitioner_name("Dr Alice  Nakato") == "alice nakato"

    def test_punctuation_collapses(self):
        assert normalise_practitioner_name("NAKATO, Alice-Jane") == "nakato alice jane"

    def test_multiple_titles_are_stripped(self):
        assert normalise_practitioner_name("Prof. Dr Alice Nakato") == "alice nakato"

    def test_a_title_inside_the_name_is_kept(self):
        """Only leading titles are stripped; a surname is not a title."""
        assert normalise_practitioner_name("Alice Doctor") == "alice doctor"

    def test_blank_and_punctuation_only_are_not_usable(self):
        assert normalise_practitioner_name("   ") == ""
        assert normalise_practitioner_name("---") == ""
        assert is_usable_name("-") is False

    def test_a_title_alone_is_not_a_usable_name(self):
        """ "Dr" on its own names nobody, so it must not become a lookup key."""
        assert normalise_practitioner_name("Dr.") == ""
        assert is_usable_name("Dr.") is False


class TestStates:
    def test_a_new_alias_is_unmapped_with_no_practitioner(self):
        alias = _alias()
        assert alias.state is AliasResolutionState.UNMAPPED
        assert alias.provider_id is None

    def test_resolving_records_who_decided(self):
        alias = _alias()
        alias.resolve(ProviderId("prov-1"), ACTOR, at=AT)
        assert alias.state is AliasResolutionState.RESOLVED
        assert alias.provider_id == ProviderId("prov-1")
        assert alias.resolved_by == ACTOR
        assert alias.resolved_at == AT

    def test_ambiguous_keeps_candidates_and_no_practitioner(self):
        alias = _alias()
        alias.mark_ambiguous(("prov-1", "prov-2"), at=AT)
        assert alias.state is AliasResolutionState.AMBIGUOUS
        assert alias.candidate_provider_ids == ("prov-1", "prov-2")
        assert alias.provider_id is None

    def test_ambiguous_requires_more_than_one_candidate(self):
        """A single candidate is not ambiguous; it still needs an explicit decision."""
        with pytest.raises(DomainError):
            _alias().mark_ambiguous(("prov-1",), at=AT)

    def test_unmapped_and_ambiguous_are_different_states(self):
        unmapped = _alias()
        ambiguous = _alias()
        ambiguous.mark_ambiguous(("prov-1", "prov-2"), at=AT)
        assert unmapped.state is not ambiguous.state

    def test_rejecting_requires_a_note(self):
        with pytest.raises(DomainError):
            _alias().reject(ACTOR, "  ", at=AT)

    def test_rejecting_records_the_note_and_clears_candidates(self):
        alias = _alias()
        alias.mark_ambiguous(("prov-1", "prov-2"), at=AT)
        alias.reject(ACTOR, "Not a person, a workshop title", at=AT)
        assert alias.state is AliasResolutionState.REJECTED
        assert alias.candidate_provider_ids == ()
        assert alias.review_note == "Not a person, a workshop title"

    def test_resolving_emits_an_auditable_decision(self):
        alias = _alias()
        alias.resolve(ProviderId("prov-1"), ACTOR, at=AT)
        assert [type(e).__name__ for e in alias.events] == ["ProviderAliasResolved"]
        assert alias.events[0].source_value == "Dr Alice  Nakato"

    def test_rejecting_emits_an_auditable_decision(self):
        alias = _alias()
        alias.reject(ACTOR, "Workshop title, not a person", at=AT)
        assert [type(e).__name__ for e in alias.events] == ["ProviderAliasRejected"]

    def test_classification_emits_nothing(self):
        """Staging output is not a decision; see the ratchet note in test_audit_coverage."""
        unmapped = _alias()
        unmapped.mark_unmapped(at=AT)
        ambiguous = _alias()
        ambiguous.mark_ambiguous(("prov-1", "prov-2"), at=AT)
        assert unmapped.events == [] and ambiguous.events == []

    def test_the_raw_source_value_is_never_rewritten(self):
        alias = _alias()
        alias.resolve(ProviderId("prov-1"), ACTOR, at=AT)
        assert alias.source_value == "Dr Alice  Nakato"


class TestInvariants:
    def test_resolved_without_a_practitioner_is_rejected(self):
        with pytest.raises(DomainError):
            _alias(state=AliasResolutionState.RESOLVED)

    def test_unresolved_with_a_practitioner_is_rejected(self):
        """Guards against a name match being persisted as a decision."""
        with pytest.raises(DomainError):
            _alias(state=AliasResolutionState.UNMAPPED, provider_id=ProviderId("prov-1"))

    def test_a_blank_source_system_is_rejected(self):
        with pytest.raises(DomainError):
            _alias(source_system=" ")
