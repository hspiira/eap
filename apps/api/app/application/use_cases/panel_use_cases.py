"""Provider panel-management use cases (Phase 4 #D-Provider).

Bulk operations supporting the 80→8 panel cull, audited tier changes, and
the eligibility check that gates new assignments. The Person aggregate emits
``ProviderPanelStatusChanged`` / ``ProviderTierChanged`` events; the events
ride out via the outbox + audit handler chain that's already in place.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from app.domain.entities.person import PersonEntity
from app.domain.enums import PanelStatus, ProviderTier
from app.domain.exceptions import DomainError, NotFoundError
from app.domain.repositories.non_compete_clause_repository import (
    NonCompeteClauseRepository,
)
from app.domain.repositories.person_repository import PersonRepository
from app.domain.value_objects.core import (
    ClientId,
    PersonId,
    TenantId,
    UserId,
)


@dataclass
class BulkPanelStatusResult:
    """Per-provider outcome of a bulk panel-status flip."""

    updated: list[str]
    skipped_no_change: list[str]
    not_found: list[str]
    not_provider: list[str]


class BulkUpdatePanelStatusUseCase:
    """Flip ``panel_status`` for a batch of providers in one call (audit-trailed).

    Skips providers already at the target status (idempotent), records 404s for
    unknown ids, and rejects non-providers — all returned in the result rather
    than raising, so the operator can act on the partial outcome.
    """

    def __init__(self, repository: PersonRepository):
        self._repo = repository

    async def execute(
        self,
        *,
        tenant_id: TenantId,
        provider_ids: list[PersonId],
        new_status: PanelStatus,
        actor: UserId,
        reason: str,
    ) -> BulkPanelStatusResult:
        if not reason:
            raise DomainError("Bulk panel-status change requires a reason")
        if not provider_ids:
            raise DomainError("provider_ids must be non-empty")

        result = BulkPanelStatusResult(
            updated=[], skipped_no_change=[], not_found=[], not_provider=[]
        )
        for pid in provider_ids:
            person = await self._repo.get_by_id(pid)
            if person is None:
                result.not_found.append(pid.value)
                continue
            if person.tenant_id != tenant_id:
                result.not_found.append(pid.value)
                continue
            if person.provider_profile is None:
                result.not_provider.append(pid.value)
                continue
            if person.provider_profile.panel_status == new_status:
                result.skipped_no_change.append(pid.value)
                continue
            person.change_panel_status(new_status=new_status, actor=actor, reason=reason)
            await self._repo.save(person)
            result.updated.append(pid.value)
        return result


class ChangeProviderTierUseCase:
    """Audited single-provider tier change."""

    def __init__(self, repository: PersonRepository):
        self._repo = repository

    async def execute(
        self,
        *,
        tenant_id: TenantId,
        provider_id: PersonId,
        new_tier: ProviderTier,
        actor: UserId,
        reason: str,
    ) -> PersonEntity:
        person = await self._repo.get_by_id(provider_id)
        if person is None or person.tenant_id != tenant_id:
            raise NotFoundError(
                f"Provider not found: {provider_id.value}",
                resource_type="Person",
                resource_id=provider_id.value,
            )
        if person.provider_profile is None:
            raise DomainError("Person is not a service provider (no panel profile)")
        person.change_tier(new_tier=new_tier, actor=actor, reason=reason)
        await self._repo.save(person)
        return person


class CheckProviderEligibilityUseCase:
    """Pre-assignment gate: panel + accreditation + binding non-compete check.

    v1 treats any binding non-compete clause as a blanket restriction (the
    clause carries no per-client list yet). The result is structured so the UI
    can render *why* a provider is ineligible rather than just hiding them.
    """

    def __init__(
        self,
        person_repository: PersonRepository,
        non_compete_repository: NonCompeteClauseRepository,
    ):
        self._people = person_repository
        self._clauses = non_compete_repository

    async def execute(
        self,
        *,
        tenant_id: TenantId,
        provider_id: PersonId,
        client_id: ClientId | None = None,
    ) -> dict[str, Any]:
        person = await self._people.get_by_id(provider_id)
        if person is None or person.tenant_id != tenant_id:
            raise NotFoundError(
                f"Provider not found: {provider_id.value}",
                resource_type="Person",
                resource_id=provider_id.value,
            )
        profile = person.provider_profile
        panel_eligible = profile is not None and profile.is_panel_eligible()
        clauses = await self._clauses.list_for_provider(tenant_id, provider_id)
        binding = [c for c in clauses if c.is_currently_binding()]
        reasons: list[str] = []
        if profile is None:
            reasons.append("Person has no provider panel profile")
        else:
            if not panel_eligible:
                reasons.append(
                    f"Panel-ineligible: status={profile.panel_status.value}, "
                    f"accreditation={profile.accreditation_status.value}"
                )
        if binding:
            reasons.append(
                f"{len(binding)} binding non-compete clause(s) — verify scope before assignment"
            )
        return {
            "provider_id": provider_id.value,
            "client_id": client_id.value if client_id else None,
            "panel_eligible": panel_eligible,
            "binding_non_compete_count": len(binding),
            "binding_non_compete_ids": [c.id.value for c in binding],
            "eligible": panel_eligible and not binding,
            "reasons": reasons,
        }
