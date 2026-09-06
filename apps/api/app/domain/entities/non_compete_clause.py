"""Non-compete clause entity (Phase 2 #D-Provider / SAD §5.2.4).

Tracks the contractual restriction on a provider taking direct work from
Minet's clients outside the platform. Drafted by legal (the actual clause
text lives in a separate document); this entity records the lifecycle and
attestation.
"""

from dataclasses import dataclass, field
from datetime import date, datetime

from app.domain.enums import NonCompeteStatus
from app.domain.events import DomainEvent
from app.domain.exceptions import DomainError
from app.domain.value_objects.core import (
    NonCompeteClauseId,
    ProviderId,
    TenantId,
    UserId,
)
from app.shared.utils.datetime import utc_now


@dataclass
class NonCompeteClauseEntity:
    """A signed non-compete agreement between Minet and a provider."""

    id: NonCompeteClauseId
    tenant_id: TenantId
    provider_id: ProviderId
    status: NonCompeteStatus
    terms_summary: str
    effective_from: date
    effective_until: date | None
    created_at: datetime
    updated_at: datetime
    signed_at: datetime | None = None
    signed_by: UserId | None = None
    revoked_at: datetime | None = None
    revoked_reason: str | None = None
    document_id: str | None = None
    events: list[DomainEvent] = field(default_factory=list[DomainEvent])

    def __post_init__(self) -> None:
        if not self.terms_summary:
            raise DomainError("Non-compete clause requires a terms summary")
        if self.effective_until and self.effective_until < self.effective_from:
            raise DomainError("effective_until must be on or after effective_from")

    def sign(self, signed_by: UserId, now: datetime | None = None) -> None:
        if self.status != NonCompeteStatus.DRAFT:
            raise DomainError(f"Cannot sign clause in status {self.status.value}")
        now = now or utc_now()
        self.status = NonCompeteStatus.ACTIVE
        self.signed_at = now
        self.signed_by = signed_by
        self.updated_at = now

    def revoke(self, reason: str, now: datetime | None = None) -> None:
        if not reason:
            raise DomainError("Revoking a clause requires a reason")
        if self.status not in {NonCompeteStatus.DRAFT, NonCompeteStatus.ACTIVE}:
            raise DomainError(f"Cannot revoke clause in status {self.status.value}")
        now = now or utc_now()
        self.status = NonCompeteStatus.REVOKED
        self.revoked_at = now
        self.revoked_reason = reason
        self.updated_at = now

    def mark_expired_if_due(self, today: date | None = None) -> None:
        """Idempotent: flips ACTIVE → EXPIRED once `effective_until` passes."""
        today = today or utc_now().date()
        if (
            self.status == NonCompeteStatus.ACTIVE
            and self.effective_until is not None
            and self.effective_until < today
        ):
            self.status = NonCompeteStatus.EXPIRED
            self.updated_at = utc_now()

    def is_currently_binding(self, today: date | None = None) -> bool:
        today = today or utc_now().date()
        if self.status != NonCompeteStatus.ACTIVE:
            return False
        if self.effective_from > today:
            return False
        if self.effective_until is not None and self.effective_until < today:
            return False
        return True
