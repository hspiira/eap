"""Utilisation event entity (Phase 2 #D-Pricing).

A billable activity tracked against a contract. Created by the source flow
(session completion, callback outreach, incident response, etc.) and
consumed by :class:`PricingEngine` to compute invoice previews.
"""

from dataclasses import dataclass
from datetime import date, datetime

from app.domain.exceptions import DomainError
from app.domain.value_objects.core import (
    ContractId,
    TenantId,
    UtilisationEventId,
)


@dataclass
class UtilisationEventEntity:
    id: UtilisationEventId
    tenant_id: TenantId
    contract_id: ContractId
    event_type: str
    occurred_on: date
    units: int
    service_code: str | None
    source_id: str | None
    notes: str | None
    created_at: datetime
    updated_at: datetime

    def __post_init__(self) -> None:
        if self.units <= 0:
            raise DomainError("Utilisation event must have positive units")
