"""Per-case session-cap authorization (benefit ledger).

Instantiated from a ``ProgrammeSessionCap`` when a Case is opened, an
``Authorization`` carries the runtime ``sessions_remaining`` for one
``(case, service_category)`` pair plus the cap snapshot at instantiation so
later programme changes don't retroactively rewrite consumed benefits.
"""

from dataclasses import dataclass, field
from datetime import date, datetime

from app.domain.enums import AuthorizationStatus
from app.domain.events import (
    AuthorizationConsumed,
    AuthorizationExtended,
    AuthorizationExtensionRequested,
    AuthorizationGranted,
    DomainEvent,
)
from app.domain.exceptions import DomainError, InvalidStateError
from app.domain.value_objects.core import (
    AuthorizationId,
    CaseId,
    ClinicalSubjectId,
    EAPProgrammeId,
    TenantId,
    UserId,
)
from app.shared.utils.datetime import utc_now


@dataclass
class Authorization:
    id: AuthorizationId
    tenant_id: TenantId
    case_id: CaseId
    clinical_subject_id: ClinicalSubjectId
    programme_id: EAPProgrammeId
    service_category: str
    sessions_granted: int
    sessions_used: int
    status: AuthorizationStatus
    granted_at: datetime
    created_at: datetime
    updated_at: datetime
    expires_on: date | None = None
    extension_requested_sessions: int | None = None
    extension_requested_by: UserId | None = None
    extension_requested_at: datetime | None = None
    extension_clinician_signoff: UserId | None = None
    extension_admin_signoff: UserId | None = None
    extended_at: datetime | None = None
    closed_at: datetime | None = None
    events: list[DomainEvent] = field(default_factory=list[DomainEvent])

    def __post_init__(self) -> None:
        if self.sessions_granted < 0:
            raise DomainError("sessions_granted cannot be negative")
        if self.sessions_used < 0:
            raise DomainError("sessions_used cannot be negative")
        if self.sessions_used > self.sessions_granted:
            raise DomainError("sessions_used cannot exceed sessions_granted")
        if self.created_at == self.updated_at and not self.events:
            self.events.append(
                AuthorizationGranted(
                    occurred_at=self.granted_at,
                    authorization_id=self.id,
                    case_id=self.case_id,
                    sessions_granted=self.sessions_granted,
                )
            )

    @property
    def sessions_remaining(self) -> int:
        return max(0, self.sessions_granted - self.sessions_used)

    def is_expired(self, *, today: date | None = None) -> bool:
        if self.expires_on is None:
            return False
        return self.expires_on < (today or utc_now().date())

    def is_active(self) -> bool:
        return self.status in {
            AuthorizationStatus.ACTIVE,
            AuthorizationStatus.EXTENSION_REQUESTED,
            AuthorizationStatus.EXTENDED,
        }

    def consume_session(self, *, now: datetime | None = None) -> None:
        if not self.is_active():
            raise InvalidStateError(f"Cannot consume from a {self.status.value} authorization")
        if self.is_expired():
            self.status = AuthorizationStatus.EXPIRED
            self.updated_at = now or utc_now()
            raise InvalidStateError("Authorization expired")
        if self.sessions_remaining <= 0:
            self.status = AuthorizationStatus.EXHAUSTED
            self.updated_at = now or utc_now()
            raise DomainError("Authorization exhausted")
        now = now or utc_now()
        self.sessions_used += 1
        if self.sessions_remaining == 0:
            self.status = AuthorizationStatus.EXHAUSTED
        self.updated_at = now
        self.events.append(
            AuthorizationConsumed(
                occurred_at=now,
                authorization_id=self.id,
                sessions_remaining=self.sessions_remaining,
            )
        )

    def request_extension(
        self,
        *,
        additional_sessions: int,
        requested_by: UserId,
        now: datetime | None = None,
    ) -> None:
        if additional_sessions <= 0:
            raise DomainError("additional_sessions must be positive")
        if self.status not in {
            AuthorizationStatus.ACTIVE,
            AuthorizationStatus.EXHAUSTED,
        }:
            raise InvalidStateError(
                f"Cannot request extension on a {self.status.value} authorization"
            )
        now = now or utc_now()
        self.status = AuthorizationStatus.EXTENSION_REQUESTED
        self.extension_requested_sessions = additional_sessions
        self.extension_requested_by = requested_by
        self.extension_requested_at = now
        self.updated_at = now
        self.events.append(
            AuthorizationExtensionRequested(
                occurred_at=now,
                authorization_id=self.id,
                requested_additional_sessions=additional_sessions,
            )
        )

    def grant_extension(
        self,
        *,
        clinician_signoff: UserId,
        admin_signoff: UserId,
        now: datetime | None = None,
    ) -> None:
        if self.status != AuthorizationStatus.EXTENSION_REQUESTED:
            raise InvalidStateError("Only EXTENSION_REQUESTED authorizations can be extended")
        if not self.extension_requested_sessions:
            raise DomainError("No pending extension to grant")
        now = now or utc_now()
        self.sessions_granted += self.extension_requested_sessions
        self.extension_clinician_signoff = clinician_signoff
        self.extension_admin_signoff = admin_signoff
        self.extended_at = now
        self.status = AuthorizationStatus.EXTENDED
        self.updated_at = now
        granted_extra = self.extension_requested_sessions
        self.extension_requested_sessions = None
        self.events.append(
            AuthorizationExtended(
                occurred_at=now,
                authorization_id=self.id,
                additional_sessions=granted_extra,
            )
        )

    def close(self, *, now: datetime | None = None) -> None:
        if self.status == AuthorizationStatus.CLOSED:
            return
        now = now or utc_now()
        self.status = AuthorizationStatus.CLOSED
        self.closed_at = now
        self.updated_at = now
