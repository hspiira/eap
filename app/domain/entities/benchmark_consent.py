"""Benchmark consent aggregate (Phase 4 #D-Benchmark / SAD A-19).

Records a tenant's opt-in to cross-tenant benchmarking. One row per tenant per
``BenchmarkScope`` — withdrawing one scope does not affect others. Each consent
carries an immutable ``version`` referring to the legal text the operator
agreed to; superseding the agreement creates a new row rather than mutating.
"""

from dataclasses import dataclass, field
from datetime import datetime

from app.domain.enums import BenchmarkScope, TenantConsentStatus
from app.domain.events import DomainEvent
from app.domain.exceptions import DomainError, InvalidStateError
from app.domain.value_objects.core import (
    BenchmarkConsentId,
    TenantId,
    UserId,
)
from app.shared.utils.datetime import utc_now


@dataclass
class BenchmarkConsent:
    """A tenant's opt-in to share benchmark-quality metrics under one scope."""

    id: BenchmarkConsentId
    tenant_id: TenantId
    scope: BenchmarkScope
    status: TenantConsentStatus
    version: str
    granted_by: UserId
    granted_at: datetime
    created_at: datetime
    updated_at: datetime
    withdrawn_at: datetime | None = None
    withdrawn_by: UserId | None = None
    withdrawn_reason: str | None = None
    events: list[DomainEvent] = field(default_factory=list[DomainEvent])

    def __post_init__(self) -> None:
        if not self.version:
            raise DomainError("BenchmarkConsent requires a version")
        if (
            self.status == TenantConsentStatus.WITHDRAWN
            and self.withdrawn_at is None
        ):
            raise DomainError(
                "Withdrawn consent must carry withdrawn_at"
            )

    def withdraw(
        self,
        *,
        actor: UserId,
        reason: str,
        now: datetime | None = None,
    ) -> None:
        if self.status != TenantConsentStatus.ACTIVE:
            raise InvalidStateError(
                f"Cannot withdraw consent in status {self.status.value}"
            )
        if not reason:
            raise DomainError("Withdrawal requires a reason")
        now = now or utc_now()
        self.status = TenantConsentStatus.WITHDRAWN
        self.withdrawn_at = now
        self.withdrawn_by = actor
        self.withdrawn_reason = reason
        self.updated_at = now

    def is_currently_consented(self) -> bool:
        return self.status == TenantConsentStatus.ACTIVE
