"""Resolve a source practitioner name to a practitioner, or to a review outcome.

Decision 5 is explicit that normalization is not proof of identity. This
service therefore only ever reads a decision that a person already recorded in
the alias table. It never creates a practitioner, never creates a placeholder,
and never promotes a single name match to a resolution.
"""

from dataclasses import dataclass
from enum import Enum

from app.domain.entities.provider_alias import ProviderAliasEntity
from app.domain.enums.provider_network import AliasResolutionState
from app.domain.repositories.provider_network_repository import ProviderAliasRepository
from app.domain.services.provider_alias_normalisation import (
    is_usable_name,
    normalise_practitioner_name,
)
from app.domain.value_objects.core import ProviderId, TenantId


class NameOutcome(str, Enum):
    """Why a source name did or did not resolve. Each is a distinct outcome."""

    RESOLVED = "Resolved"
    MISSING = "Missing"
    UNMAPPED = "Unmapped"
    AMBIGUOUS = "Ambiguous"
    REJECTED = "Rejected"


@dataclass(frozen=True)
class NameResolution:
    outcome: NameOutcome
    provider_id: ProviderId | None = None
    normalized_value: str = ""
    reasons: tuple[str, ...] = ()

    @property
    def is_resolved(self) -> bool:
        return self.outcome is NameOutcome.RESOLVED


_STATE_OUTCOMES = {
    AliasResolutionState.RESOLVED: NameOutcome.RESOLVED,
    AliasResolutionState.AMBIGUOUS: NameOutcome.AMBIGUOUS,
    AliasResolutionState.UNMAPPED: NameOutcome.UNMAPPED,
    AliasResolutionState.REJECTED: NameOutcome.REJECTED,
}


class ProviderAliasReconciliationService:
    def __init__(self, aliases: ProviderAliasRepository):
        self._aliases = aliases
        # Scoped to one request, so it cannot go stale between them.
        self._alias_cache: dict[tuple[str, str], ProviderAliasEntity | None] = {}

    async def resolve(
        self, tenant_id: TenantId, source_system: str, raw_name: str | None
    ) -> NameResolution:
        """Look up an existing reconciliation decision for this source name.

        A name with no alias row is `UNMAPPED`, which is different from a row
        that is absent from the source entirely (`MISSING`) and different again
        from a row a person has reviewed and found ambiguous.
        """
        if raw_name is None or not is_usable_name(raw_name):
            return NameResolution(
                outcome=NameOutcome.MISSING,
                reasons=("No practitioner name in the source row",),
            )
        normalized = normalise_practitioner_name(raw_name)
        alias = await self._find_alias(tenant_id, source_system, normalized)
        if alias is None:
            return NameResolution(
                outcome=NameOutcome.UNMAPPED,
                normalized_value=normalized,
                reasons=(f"No alias mapping for {raw_name!r} in {source_system}",),
            )
        return self._from_alias(alias, raw_name, normalized)

    async def _find_alias(
        self, tenant_id: TenantId, source_system: str, normalized: str
    ) -> ProviderAliasEntity | None:
        key = (source_system, normalized)
        if key not in self._alias_cache:
            self._alias_cache[key] = await self._aliases.find_alias(
                tenant_id, source_system, normalized
            )
        return self._alias_cache[key]

    def _from_alias(
        self, alias: ProviderAliasEntity, raw_name: str, normalized: str
    ) -> NameResolution:
        outcome = _STATE_OUTCOMES[alias.state]
        if outcome is NameOutcome.RESOLVED:
            return NameResolution(
                outcome=outcome, provider_id=alias.provider_id, normalized_value=normalized
            )
        return NameResolution(
            outcome=outcome,
            normalized_value=normalized,
            reasons=(_review_reason(alias, raw_name),),
        )


def _review_reason(alias: ProviderAliasEntity, raw_name: str) -> str:
    if alias.state is AliasResolutionState.AMBIGUOUS:
        candidates = ", ".join(alias.candidate_provider_ids)
        return f"{raw_name!r} matches several practitioners: {candidates}"
    if alias.state is AliasResolutionState.REJECTED:
        return f"{raw_name!r} was reviewed and is not a practitioner: {alias.review_note}"
    return f"{raw_name!r} has an alias awaiting reconciliation"
