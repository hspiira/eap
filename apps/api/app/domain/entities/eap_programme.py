"""EAP programme aggregate.

Represents the benefit package one ``Contract`` purchases on behalf of its
eligible members: which service categories are included, with what session
caps, over what coverage window. The ``Authorization`` aggregate is the
runtime ledger of those caps against an open ``Case``.
"""

from dataclasses import dataclass, field
from datetime import date, datetime

from app.domain.enums import RelationType
from app.domain.events import DomainEvent, EAPProgrammeCreated
from app.domain.exceptions import DomainError
from app.domain.value_objects.core import (
    ContractId,
    EAPProgrammeId,
    TenantId,
    UserId,
)
from app.domain.value_objects.programme import ProgrammeSessionCap
from app.shared.utils.datetime import utc_now


@dataclass
class EAPProgramme:
    id: EAPProgrammeId
    tenant_id: TenantId
    contract_id: ContractId
    name: str
    effective_from: date
    caps: tuple[ProgrammeSessionCap, ...]
    eligible_dependent_relations: tuple[RelationType, ...]
    created_at: datetime
    updated_at: datetime
    effective_until: date | None = None
    geographic_scope: str | None = None
    description: str | None = None
    created_by: UserId | None = None
    is_active: bool = True
    events: list[DomainEvent] = field(default_factory=list[DomainEvent])

    def __post_init__(self) -> None:
        if not self.name:
            raise DomainError("EAPProgramme requires a name")
        if not self.caps:
            raise DomainError("EAPProgramme requires at least one session cap")
        if self.effective_until and self.effective_until < self.effective_from:
            raise DomainError("effective_until must be on or after effective_from")
        seen: set[str] = set()
        for cap in self.caps:
            if cap.service_category in seen:
                raise DomainError(f"Duplicate cap for {cap.service_category}")
            seen.add(cap.service_category)
        if self.created_at == self.updated_at and not self.events:
            self.events.append(
                EAPProgrammeCreated(
                    occurred_at=self.created_at,
                    programme_id=self.id,
                    tenant_id=self.tenant_id,
                    contract_id=self.contract_id,
                )
            )

    def cap_for(self, service_category: str) -> ProgrammeSessionCap | None:
        for cap in self.caps:
            if cap.service_category == service_category:
                return cap
        return None

    def is_currently_effective(self, *, today: date | None = None) -> bool:
        today = today or utc_now().date()
        if not self.is_active:
            return False
        if self.effective_from > today:
            return False
        if self.effective_until is not None and self.effective_until < today:
            return False
        return True

    def deactivate(self, *, now: datetime | None = None) -> None:
        if not self.is_active:
            return
        now = now or utc_now()
        self.is_active = False
        self.updated_at = now
