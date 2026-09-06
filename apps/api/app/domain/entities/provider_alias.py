"""Practitioner aliases, scoped by tenant and source system (decision 5)."""

from dataclasses import dataclass, field
from datetime import datetime

from app.domain.enums.provider_network import AliasResolutionState
from app.domain.events import DomainEvent
from app.domain.events.provider_network import (
    ProviderAliasRejected,
    ProviderAliasResolved,
)
from app.domain.exceptions import DomainError
from app.domain.value_objects.core import ProviderId, TenantId, UserId
from app.domain.value_objects.provider_network import ProviderAliasId


@dataclass
class ProviderAliasEntity:
    """A source-system name and the reconciliation decision made about it.

    `source_value` is the raw name as it arrived and is never rewritten.
    `normalized_value` records the normalization used for candidate matching
    and is explicitly not proof of identity: resolving to a practitioner
    requires `resolve`, which records who decided.
    """

    id: ProviderAliasId
    tenant_id: TenantId
    source_system: str
    source_value: str
    normalized_value: str
    created_at: datetime
    updated_at: datetime
    state: AliasResolutionState = AliasResolutionState.UNMAPPED
    provider_id: ProviderId | None = None
    candidate_provider_ids: tuple[str, ...] = ()
    resolved_by: UserId | None = None
    resolved_at: datetime | None = None
    review_note: str | None = None
    events: list[DomainEvent] = field(default_factory=list["DomainEvent"])

    def __post_init__(self) -> None:
        if not self.source_system or not self.source_system.strip():
            raise DomainError("Alias requires a source system")
        if not self.source_value or not self.source_value.strip():
            raise DomainError("Alias requires a source value")
        if self.state is AliasResolutionState.RESOLVED and self.provider_id is None:
            raise DomainError("A resolved alias requires a practitioner")
        if self.state is not AliasResolutionState.RESOLVED and self.provider_id is not None:
            raise DomainError("Only a resolved alias may name a practitioner")

    def resolve(self, provider_id: ProviderId, actor: UserId, *, at: datetime) -> None:
        """Record an explicit reconciliation decision.

        Never called automatically from name matching; decision 5 requires a
        person to choose, including when only one candidate was found.
        """
        self.provider_id = provider_id
        self.state = AliasResolutionState.RESOLVED
        self.resolved_by = actor
        self.resolved_at = at
        self.updated_at = at
        self.events.append(
            ProviderAliasResolved(
                occurred_at=at,
                alias_id=self.id,
                tenant_id=self.tenant_id,
                source_system=self.source_system,
                source_value=self.source_value,
                provider_id=provider_id,
                actor=actor,
            )
        )

    def mark_ambiguous(self, candidates: tuple[str, ...], *, at: datetime) -> None:
        """Several candidates and no decision. Distinct from unmapped.

        Deliberately emits no event: this is the staging classifier's output,
        not a human decision, and one event per unmatched name would flood the
        audit log for a file of several thousand rows. The reviewable state and
        its candidates are persisted on the row, and `resolve` and `reject`,
        which are decisions, do emit.
        """
        if len(candidates) < 2:
            raise DomainError("Ambiguous alias requires at least two candidates")
        self.state = AliasResolutionState.AMBIGUOUS
        self.candidate_provider_ids = candidates
        self.provider_id = None
        self.updated_at = at

    def mark_unmapped(self, *, at: datetime) -> None:
        """No candidate at all. Distinct from ambiguous."""
        self.state = AliasResolutionState.UNMAPPED
        self.candidate_provider_ids = ()
        self.provider_id = None
        self.updated_at = at

    def reject(self, actor: UserId, note: str, *, at: datetime) -> None:
        """Record that this source value is not a practitioner."""
        if not note or not note.strip():
            raise DomainError("Rejecting an alias requires a note")
        self.state = AliasResolutionState.REJECTED
        self.provider_id = None
        self.candidate_provider_ids = ()
        self.resolved_by = actor
        self.resolved_at = at
        self.review_note = note
        self.updated_at = at
        self.events.append(
            ProviderAliasRejected(
                occurred_at=at,
                alias_id=self.id,
                tenant_id=self.tenant_id,
                source_system=self.source_system,
                source_value=self.source_value,
                actor=actor,
                reason=note,
            )
        )

    def clear_events(self) -> None:
        self.events.clear()
