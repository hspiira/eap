"""Tenant Data Protection Officer (DPO) contact record.

Each tenant must designate a DPO whose contact details we surface to the
regulator on request. Singleton-per-tenant by convention — the use case
``UpsertDPOContact`` keeps the latest record, archiving prior ones with an
``effective_until`` so the regulator can audit who held the role when.
"""

from dataclasses import dataclass, field
from datetime import date, datetime

from app.domain.events import DomainEvent
from app.domain.exceptions import DomainError
from app.domain.value_objects.core import (
    DPOContactId,
    Email,
    TenantId,
    UserId,
)


@dataclass
class DPOContact:
    id: DPOContactId
    tenant_id: TenantId
    full_name: str
    email: Email
    effective_from: date
    created_at: datetime
    updated_at: datetime
    phone: str | None = None
    role_title: str | None = None
    effective_until: date | None = None
    appointed_by: UserId | None = None
    events: list[DomainEvent] = field(default_factory=list[DomainEvent])

    def __post_init__(self) -> None:
        if not self.full_name:
            raise DomainError("DPOContact requires a full_name")
        if (
            self.effective_until is not None
            and self.effective_until < self.effective_from
        ):
            raise DomainError(
                "effective_until must be on or after effective_from"
            )

    def archive(
        self, *, ending_on: date, now: datetime | None = None
    ) -> None:
        if self.effective_until is not None:
            raise DomainError("DPOContact already archived")
        if ending_on < self.effective_from:
            raise DomainError(
                "ending_on must be on or after effective_from"
            )
        self.effective_until = ending_on
        from app.shared.utils.datetime import utc_now as _now

        self.updated_at = now or _now()
