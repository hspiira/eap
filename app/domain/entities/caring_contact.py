"""Caring-contact scheduled follow-up.

Automatically created in a 24h / 7d / 30d cadence after any crisis-flagged
event. The aggregate is the *task*: a counsellor (or the auto-dispatcher)
records the outcome once the contact is attempted. Outcomes never feed back
into the case chart directly — that's the job of the clinical note authored
during the contact.
"""

from dataclasses import dataclass, field
from datetime import datetime, timedelta

from app.domain.enums import CaringContactChannel, CaringContactOutcome
from app.domain.events import (
    CaringContactCompleted,
    CaringContactScheduled,
    DomainEvent,
)
from app.domain.exceptions import DomainError, InvalidStateError
from app.domain.value_objects.core import (
    CaringContactId,
    CaseId,
    ClinicalSubjectId,
    CrisisContactId,
    TenantId,
    UserId,
)
from app.shared.utils.datetime import utc_now


CARING_CONTACT_CADENCE: tuple[timedelta, ...] = (
    timedelta(hours=24),
    timedelta(days=7),
    timedelta(days=30),
)


@dataclass
class CaringContact:
    id: CaringContactId
    tenant_id: TenantId
    clinical_subject_id: ClinicalSubjectId
    crisis_contact_id: CrisisContactId
    channel: CaringContactChannel
    due_at: datetime
    outcome: CaringContactOutcome
    created_at: datetime
    updated_at: datetime
    case_id: CaseId | None = None
    attempted_at: datetime | None = None
    completed_at: datetime | None = None
    handled_by: UserId | None = None
    notes: str | None = None
    events: list[DomainEvent] = field(default_factory=list)

    def __post_init__(self) -> None:
        if self.created_at == self.updated_at and not self.events:
            self.events.append(
                CaringContactScheduled(
                    occurred_at=self.created_at,
                    caring_contact_id=self.id,
                    due_at=self.due_at,
                )
            )

    def is_pending(self) -> bool:
        return self.outcome == CaringContactOutcome.PENDING

    def record_outcome(
        self,
        *,
        outcome: CaringContactOutcome,
        handled_by: UserId,
        notes: str | None = None,
        now: datetime | None = None,
    ) -> None:
        if outcome == CaringContactOutcome.PENDING:
            raise DomainError("record_outcome requires a terminal outcome")
        if not self.is_pending():
            raise InvalidStateError(
                "Caring-contact outcome has already been recorded"
            )
        now = now or utc_now()
        self.outcome = outcome
        self.handled_by = handled_by
        self.notes = notes
        self.attempted_at = self.attempted_at or now
        self.completed_at = now
        self.updated_at = now
        self.events.append(
            CaringContactCompleted(
                occurred_at=now,
                caring_contact_id=self.id,
                outcome=outcome.value,
            )
        )
