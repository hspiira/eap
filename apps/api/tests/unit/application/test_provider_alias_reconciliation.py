"""Reconciliation reads recorded decisions; it never infers identity."""

from unittest.mock import AsyncMock

from app.application.services.provider_alias_reconciliation import (
    NameOutcome,
    ProviderAliasReconciliationService,
)
from app.domain.entities.provider_alias import ProviderAliasEntity
from app.domain.enums.provider_network import AliasResolutionState
from app.domain.value_objects.core import ProviderId, TenantId
from app.domain.value_objects.provider_network import ProviderAliasId
from app.shared.utils.datetime import utc_now

TENANT = TenantId("t-1")
SOURCE = "sessions-csv"


def _alias(**overrides) -> ProviderAliasEntity:
    now = utc_now()
    defaults = {
        "id": ProviderAliasId("al-1"),
        "tenant_id": TENANT,
        "source_system": SOURCE,
        "source_value": "Dr Alice Nakato",
        "normalized_value": "alice nakato",
        "created_at": now,
        "updated_at": now,
    }
    return ProviderAliasEntity(**{**defaults, **overrides})


def _service(alias=None):
    aliases = AsyncMock()
    aliases.find_alias.return_value = alias
    return ProviderAliasReconciliationService(aliases), aliases


class TestMissingVersusUnmapped:
    async def test_no_name_at_all_is_missing(self):
        service, aliases = _service()
        result = await service.resolve(TENANT, SOURCE, None)
        assert result.outcome is NameOutcome.MISSING
        aliases.find_alias.assert_not_awaited()

    async def test_a_blank_name_is_missing_not_unmapped(self):
        service, _ = _service()
        assert (await service.resolve(TENANT, SOURCE, "   ")).outcome is NameOutcome.MISSING

    async def test_a_title_alone_is_missing(self):
        """ "Dr." normalises to nothing, so it names nobody and is not a lookup."""
        service, aliases = _service()
        result = await service.resolve(TENANT, SOURCE, "Dr.")
        assert result.outcome is NameOutcome.MISSING
        aliases.find_alias.assert_not_awaited()

    async def test_a_usable_name_with_no_alias_row_is_unmapped(self):
        service, _ = _service(alias=None)
        result = await service.resolve(TENANT, SOURCE, "Dr Alice Nakato")
        assert result.outcome is NameOutcome.UNMAPPED
        assert result.provider_id is None
        assert "Dr Alice Nakato" in result.reasons[0]


class TestRecordedDecisions:
    async def test_a_resolved_alias_returns_the_practitioner(self):
        service, _ = _service(
            alias=_alias(state=AliasResolutionState.RESOLVED, provider_id=ProviderId("prov-1"))
        )
        result = await service.resolve(TENANT, SOURCE, "Dr Alice Nakato")
        assert result.is_resolved
        assert result.provider_id == ProviderId("prov-1")

    async def test_an_ambiguous_alias_names_its_candidates(self):
        service, _ = _service(
            alias=_alias(
                state=AliasResolutionState.AMBIGUOUS,
                candidate_provider_ids=("prov-1", "prov-2"),
            )
        )
        result = await service.resolve(TENANT, SOURCE, "Dr Alice Nakato")
        assert result.outcome is NameOutcome.AMBIGUOUS
        assert result.provider_id is None
        assert "prov-1, prov-2" in result.reasons[0]

    async def test_a_rejected_alias_reports_the_review_note(self):
        service, _ = _service(
            alias=_alias(state=AliasResolutionState.REJECTED, review_note="Workshop title")
        )
        result = await service.resolve(TENANT, SOURCE, "Dr Alice Nakato")
        assert result.outcome is NameOutcome.REJECTED
        assert "Workshop title" in result.reasons[0]

    async def test_an_unreconciled_alias_row_stays_unmapped(self):
        service, _ = _service(alias=_alias(state=AliasResolutionState.UNMAPPED))
        result = await service.resolve(TENANT, SOURCE, "Dr Alice Nakato")
        assert result.outcome is NameOutcome.UNMAPPED
        assert result.provider_id is None


class TestScoping:
    async def test_the_lookup_is_scoped_to_tenant_and_source_system(self):
        service, aliases = _service()
        await service.resolve(TENANT, "legacy-hr", "Dr Alice Nakato")
        args, _ = aliases.find_alias.call_args
        assert args[0] == TENANT
        assert args[1] == "legacy-hr"
        assert args[2] == "alice nakato"

    async def test_spelling_variants_reach_the_same_lookup_key(self):
        """Normalisation groups candidates; it does not decide identity."""
        service, aliases = _service()
        for spelling in ("Dr Alice  Nakato", "NAKATO, Alice", "alice nakato"):
            await service.resolve(TENANT, SOURCE, spelling)
        keys = {call.args[2] for call in aliases.find_alias.call_args_list}
        assert keys == {"alice nakato", "nakato alice"}
