"""Provider affiliation aggregate: a dated link between a practitioner and a firm."""

from dataclasses import dataclass, field
from datetime import date, datetime

from app.domain.events import DomainEvent
from app.domain.events.provider_network import (
    ProviderAffiliationCreated,
    ProviderAffiliationEnded,
)
from app.domain.exceptions import DomainError
from app.domain.value_objects.core import ProviderId, TenantId, UserId
from app.domain.value_objects.provider_network import (
    ProviderAffiliationId,
    ProviderOrganisationId,
)
from app.shared.utils.datetime import utc_now


@dataclass
class ProviderAffiliationEntity:
    """Validity is start-inclusive and end-exclusive: valid_from <= d < valid_until.

    A null `valid_until` is open-ended. The practitioner and organisation are
    immutable, so past session attribution cannot be repointed.
    """

    id: ProviderAffiliationId
    tenant_id: TenantId
    provider_id: ProviderId
    organisation_id: ProviderOrganisationId
    valid_from: date
    created_at: datetime
    updated_at: datetime
    valid_until: date | None = None
    events: list[DomainEvent] = field(default_factory=list["DomainEvent"])

    def __post_init__(self) -> None:
        if self.valid_until is not None and self.valid_until <= self.valid_from:
            raise DomainError("Affiliation valid_until must be after valid_from")

    def covers(self, day: date) -> bool:
        if day < self.valid_from:
            return False
        return self.valid_until is None or day < self.valid_until

    def overlaps(self, other_from: date, other_until: date | None) -> bool:
        """Half-open interval intersection for the same practitioner and firm."""
        if other_until is not None and other_until <= self.valid_from:
            return False
        if self.valid_until is not None and self.valid_until <= other_from:
            return False
        return True

    def record_created(self, actor: UserId) -> None:
        self.events.append(
            ProviderAffiliationCreated(
                occurred_at=utc_now(),
                affiliation_id=self.id,
                tenant_id=self.tenant_id,
                provider_id=self.provider_id,
                organisation_id=self.organisation_id,
                valid_from=self.valid_from,
                valid_until=self.valid_until,
                actor=actor,
            )
        )

    def change_end(self, new_valid_until: date | None, actor: UserId, reason: str) -> None:
        """Move only the end date, which is the sole mutable part of the interval."""
        if not reason or not reason.strip():
            raise DomainError("A reason is required to change an affiliation end date")
        if new_valid_until is not None and new_valid_until <= self.valid_from:
            raise DomainError("Affiliation valid_until must be after valid_from")
        if new_valid_until == self.valid_until:
            return
        old = self.valid_until
        self.valid_until = new_valid_until
        self.updated_at = utc_now()
        self.events.append(
            ProviderAffiliationEnded(
                occurred_at=self.updated_at,
                affiliation_id=self.id,
                tenant_id=self.tenant_id,
                old_valid_until=old,
                new_valid_until=new_valid_until,
                actor=actor,
                reason=reason,
            )
        )

    def clear_events(self) -> None:
        self.events.clear()
