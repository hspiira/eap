"""Outreach record entity (Phase 3 #D-CareCallback).

One row per person targeted by a campaign. Carries the assignment, contact
attempts, terminal disposition, optional triage response payload, and any
flags raised by triage scoring.
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any

from app.domain.enums import OutreachStatus, TriageRiskLevel
from app.domain.events import (
    CrisisFlagRaised,
    DomainEvent,
    OutreachAssigned,
    OutreachCompleted,
)
from app.domain.exceptions import DomainError, InvalidStateError
from app.domain.value_objects.core import (
    CareCallbackCampaignId,
    OutreachRecordId,
    PersonId,
    TenantId,
)
from app.shared.utils.datetime import utc_now


_TERMINAL_STATUSES = {
    OutreachStatus.COMPLETED,
    OutreachStatus.UNREACHABLE,
    OutreachStatus.DECLINED,
    OutreachStatus.ESCALATED,
}


@dataclass
class OutreachRecord:
    """Per-person outreach state inside a campaign."""

    id: OutreachRecordId
    tenant_id: TenantId
    campaign_id: CareCallbackCampaignId
    person_id: PersonId
    status: OutreachStatus
    contact_attempts: int
    created_at: datetime
    updated_at: datetime
    counsellor_id: PersonId | None = None
    assigned_at: datetime | None = None
    last_attempted_at: datetime | None = None
    completed_at: datetime | None = None
    triage_instrument_code: str | None = None
    triage_responses: dict[str, Any] | None = None
    triage_scores: dict[str, Any] | None = None
    triage_risk_level: TriageRiskLevel | None = None
    crisis_flag: bool = False
    notes: str | None = None
    events: list[DomainEvent] = field(default_factory=list)

    def __post_init__(self) -> None:
        if self.contact_attempts < 0:
            raise DomainError("contact_attempts cannot be negative")

    def assign(self, counsellor_id: PersonId, now: datetime | None = None) -> None:
        """Route this outreach to a counsellor."""
        if self.status in _TERMINAL_STATUSES:
            raise InvalidStateError(
                f"Cannot assign outreach in terminal status {self.status.value}"
            )
        now = now or utc_now()
        self.counsellor_id = counsellor_id
        self.assigned_at = now
        self.status = OutreachStatus.ASSIGNED
        self.updated_at = now
        self.events.append(
            OutreachAssigned(
                occurred_at=now,
                outreach_id=self.id,
                counsellor_id=counsellor_id,
            )
        )

    def record_attempt(self, now: datetime | None = None) -> None:
        """Counsellor tried to reach the person; bumps contact_attempts."""
        if self.status in _TERMINAL_STATUSES:
            raise InvalidStateError(
                f"Cannot record attempt in terminal status {self.status.value}"
            )
        if self.status == OutreachStatus.PENDING:
            raise InvalidStateError("Outreach must be assigned before contact attempts")
        now = now or utc_now()
        self.contact_attempts += 1
        self.last_attempted_at = now
        if self.status == OutreachStatus.ASSIGNED:
            self.status = OutreachStatus.CONTACTED
        self.updated_at = now

    def record_triage(
        self,
        *,
        instrument_code: str,
        responses: dict[str, Any],
        scores: dict[str, Any],
        risk_level: TriageRiskLevel,
        crisis_flag: bool,
        crisis_reason: str | None = None,
        now: datetime | None = None,
    ) -> None:
        """Attach triage payload + computed risk/crisis classification."""
        if self.status in _TERMINAL_STATUSES:
            raise InvalidStateError(
                f"Cannot record triage in terminal status {self.status.value}"
            )
        if not instrument_code:
            raise DomainError("Triage requires an instrument code")
        now = now or utc_now()
        self.triage_instrument_code = instrument_code
        self.triage_responses = dict(responses)
        self.triage_scores = dict(scores)
        self.triage_risk_level = risk_level
        self.crisis_flag = crisis_flag
        self.updated_at = now
        if crisis_flag:
            self.events.append(
                CrisisFlagRaised(
                    occurred_at=now,
                    outreach_id=self.id,
                    person_id=self.person_id,
                    risk_level=risk_level.value,
                    reason=crisis_reason or "Crisis indicator triggered by triage",
                )
            )

    def complete(self, notes: str | None = None, now: datetime | None = None) -> None:
        self._terminate(OutreachStatus.COMPLETED, notes=notes, now=now)

    def mark_unreachable(self, notes: str | None = None, now: datetime | None = None) -> None:
        self._terminate(OutreachStatus.UNREACHABLE, notes=notes, now=now)

    def mark_declined(self, notes: str | None = None, now: datetime | None = None) -> None:
        self._terminate(OutreachStatus.DECLINED, notes=notes, now=now)

    def escalate(self, notes: str, now: datetime | None = None) -> None:
        if not notes:
            raise DomainError("Escalation requires notes explaining the reason")
        self._terminate(OutreachStatus.ESCALATED, notes=notes, now=now)

    def _terminate(
        self,
        status: OutreachStatus,
        *,
        notes: str | None,
        now: datetime | None,
    ) -> None:
        if self.status in _TERMINAL_STATUSES:
            raise InvalidStateError(
                f"Outreach is already in terminal status {self.status.value}"
            )
        if self.status == OutreachStatus.PENDING:
            raise InvalidStateError("Cannot terminate a pending outreach without assignment")
        now = now or utc_now()
        self.status = status
        self.completed_at = now
        if notes:
            self.notes = notes
        self.updated_at = now
        self.events.append(
            OutreachCompleted(
                occurred_at=now,
                outreach_id=self.id,
                terminal_status=status.value,
            )
        )

    def is_terminal(self) -> bool:
        return self.status in _TERMINAL_STATUSES
