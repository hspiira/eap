"""Clinical case aggregate.

The central container that ties one episode of care together: presenting
problem, referral source, the subject (pseudonymous — see ``ClinicalSubject``),
the assigned counsellor, the lifecycle, and the rolled-up screener
administrations used at intake and closure for outcome measurement.

Sessions, clinical notes, risk assessments, safety plans and outreach records
all reference a ``Case`` by ``case_id``; a Case never directly references a
``Person`` or ``EligibleMember`` to keep the privacy wall intact.
"""

from dataclasses import dataclass, field
from datetime import datetime

from app.domain.enums import (
    CaseClosureReason,
    CaseReferralSource,
    CaseStatus,
    PresentingProblem,
)
from app.domain.events import (
    CaseAdvanced,
    CaseAssigned,
    CaseClosed,
    CaseOpened,
    DomainEvent,
)
from app.domain.exceptions import DomainError, InvalidStateError
from app.domain.value_objects.core import (
    AuthorizationId,
    CaseId,
    ClientId,
    ClinicalSubjectId,
    PersonId,
    TenantId,
    UserId,
)
from app.shared.utils.datetime import utc_now

_STATUS_TRANSITIONS: dict[CaseStatus, frozenset[CaseStatus]] = {
    CaseStatus.INTAKE: frozenset(
        {CaseStatus.ASSESSMENT, CaseStatus.NO_SHOW_CLOSED, CaseStatus.REFERRED_OUT}
    ),
    CaseStatus.ASSESSMENT: frozenset(
        {
            CaseStatus.ACTIVE,
            CaseStatus.REFERRED_OUT,
            CaseStatus.NO_SHOW_CLOSED,
            CaseStatus.CLOSED,
        }
    ),
    CaseStatus.ACTIVE: frozenset(
        {CaseStatus.CLOSED, CaseStatus.REFERRED_OUT, CaseStatus.NO_SHOW_CLOSED}
    ),
    CaseStatus.CLOSED: frozenset(),
    CaseStatus.REFERRED_OUT: frozenset(),
    CaseStatus.NO_SHOW_CLOSED: frozenset(),
}


_TERMINAL_STATUSES = frozenset(
    {CaseStatus.CLOSED, CaseStatus.REFERRED_OUT, CaseStatus.NO_SHOW_CLOSED}
)


@dataclass
class Case:
    id: CaseId
    tenant_id: TenantId
    clinical_subject_id: ClinicalSubjectId
    client_id: ClientId
    presenting_problem: PresentingProblem
    referral_source: CaseReferralSource
    status: CaseStatus
    opened_at: datetime
    created_at: datetime
    updated_at: datetime
    assigned_counsellor_id: PersonId | None = None
    authorization_id: AuthorizationId | None = None
    referred_by_user_id: UserId | None = None
    referral_notes: str | None = None
    closed_at: datetime | None = None
    closure_reason: CaseClosureReason | None = None
    closure_summary_note_id: str | None = None
    intake_screener_admin_ids: tuple[str, ...] = ()
    closure_screener_admin_ids: tuple[str, ...] = ()
    events: list[DomainEvent] = field(default_factory=list[DomainEvent])

    def __post_init__(self) -> None:
        if self.created_at == self.updated_at and not self.events:
            self.events.append(
                CaseOpened(
                    occurred_at=self.created_at,
                    case_id=self.id,
                    tenant_id=self.tenant_id,
                    clinical_subject_id=self.clinical_subject_id,
                    referral_source=self.referral_source.value,
                    presenting_problem=self.presenting_problem.value,
                )
            )

    def is_terminal(self) -> bool:
        return self.status in _TERMINAL_STATUSES

    def assign_counsellor(
        self, counsellor_id: PersonId, *, now: datetime | None = None
    ) -> None:
        if self.is_terminal():
            raise InvalidStateError(
                f"Cannot assign a counsellor on a {self.status.value} case"
            )
        now = now or utc_now()
        self.assigned_counsellor_id = counsellor_id
        self.updated_at = now
        self.events.append(
            CaseAssigned(
                occurred_at=now, case_id=self.id, counsellor_id=counsellor_id
            )
        )

    def attach_authorization(self, authorization_id: AuthorizationId) -> None:
        if self.is_terminal():
            raise InvalidStateError(
                f"Cannot attach an authorization on a {self.status.value} case"
            )
        self.authorization_id = authorization_id
        self.updated_at = utc_now()

    def record_intake_screener(self, admin_id: str) -> None:
        if not admin_id:
            raise DomainError("intake screener admin_id is required")
        if self.status not in {CaseStatus.INTAKE, CaseStatus.ASSESSMENT}:
            raise InvalidStateError(
                f"Cannot record an intake screener once status is {self.status.value}"
            )
        if admin_id not in self.intake_screener_admin_ids:
            self.intake_screener_admin_ids = (
                *self.intake_screener_admin_ids,
                admin_id,
            )
            self.updated_at = utc_now()

    def record_closure_screener(self, admin_id: str) -> None:
        if not admin_id:
            raise DomainError("closure screener admin_id is required")
        if self.status != CaseStatus.ACTIVE:
            raise InvalidStateError(
                "Closure screeners are recorded while the case is still ACTIVE, "
                + "before transitioning to CLOSED"
            )
        if admin_id not in self.closure_screener_admin_ids:
            self.closure_screener_admin_ids = (
                *self.closure_screener_admin_ids,
                admin_id,
            )
            self.updated_at = utc_now()

    def advance(self, target: CaseStatus, *, now: datetime | None = None) -> None:
        if target not in _STATUS_TRANSITIONS.get(self.status, frozenset()):
            raise InvalidStateError(
                f"Invalid transition: {self.status.value} → {target.value}"
            )
        if target == CaseStatus.ACTIVE and not self.assigned_counsellor_id:
            raise DomainError(
                "Cannot move to Active without an assigned counsellor"
            )
        now = now or utc_now()
        old = self.status
        self.status = target
        self.updated_at = now
        self.events.append(
            CaseAdvanced(
                occurred_at=now,
                case_id=self.id,
                from_status=old.value,
                to_status=target.value,
            )
        )

    def close(
        self,
        *,
        reason: CaseClosureReason,
        closure_summary_note_id: str | None = None,
        now: datetime | None = None,
    ) -> None:
        if self.status not in {
            CaseStatus.ASSESSMENT,
            CaseStatus.ACTIVE,
            CaseStatus.INTAKE,
        }:
            raise InvalidStateError(
                f"Cannot close a {self.status.value} case"
            )
        if (
            self.status == CaseStatus.ACTIVE
            and reason == CaseClosureReason.GOALS_MET
            and not self.closure_screener_admin_ids
        ):
            raise DomainError(
                "Closing an Active case with goals_met requires at least one "
                + "closure screener administration"
            )
        now = now or utc_now()
        old = self.status
        self.status = CaseStatus.CLOSED
        self.closed_at = now
        self.closure_reason = reason
        if closure_summary_note_id:
            self.closure_summary_note_id = closure_summary_note_id
        self.updated_at = now
        self.events.append(
            CaseAdvanced(
                occurred_at=now,
                case_id=self.id,
                from_status=old.value,
                to_status=CaseStatus.CLOSED.value,
            )
        )
        self.events.append(
            CaseClosed(
                occurred_at=now,
                case_id=self.id,
                closure_reason=reason.value,
            )
        )

    def refer_out(
        self,
        *,
        notes: str,
        now: datetime | None = None,
    ) -> None:
        if not notes:
            raise DomainError("refer_out requires explanatory notes")
        if self.is_terminal():
            raise InvalidStateError(
                f"Cannot refer out a {self.status.value} case"
            )
        now = now or utc_now()
        old = self.status
        self.status = CaseStatus.REFERRED_OUT
        self.closure_reason = CaseClosureReason.REFERRED_OUT
        self.referral_notes = notes
        self.closed_at = now
        self.updated_at = now
        self.events.append(
            CaseAdvanced(
                occurred_at=now,
                case_id=self.id,
                from_status=old.value,
                to_status=CaseStatus.REFERRED_OUT.value,
            )
        )
