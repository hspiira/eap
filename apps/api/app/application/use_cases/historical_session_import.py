"""The Admin-only write path for sessions that already happened.

Historical acceptance and new-booking eligibility are deliberately separate
rules. A session delivered in 2023 by a practitioner who left the panel in 2024
is a fact about the past; refusing to record it because that practitioner
cannot take new work today would discard evidence rather than protect anyone.

So this path does not consult the booking gate. What it does enforce is that
the record describes the past: the practitioner must belong to the tenant, the
session must be dated in the past, and the delivery context must be whatever
the source establishes, including Unknown when it establishes nothing.

It performs no billing, no authorization drawdown and no completion side
effects. Those belong to live delivery, not to recording what already occurred.
"""

from dataclasses import dataclass
from datetime import datetime

from app.domain.entities.provider import ProviderEntity
from app.domain.entities.service_session import ServiceSessionEntity
from app.domain.enums import (
    ClientType,
    SessionAttendance,
    SessionCategory,
    SessionClinicalStatus,
    SessionDeliveryContext,
    SessionStatus,
    SessionType,
)
from app.domain.exceptions import DomainError
from app.domain.repositories.provider_repository import ProviderRepository
from app.domain.repositories.service_session_repository import ServiceSessionRepository
from app.domain.services.provider_network_calendar import boundary_day
from app.domain.value_objects.core import (
    ClientId,
    EligibleMemberId,
    ProviderId,
    ServiceId,
    SessionId,
    TenantId,
)
from app.shared.utils.datetime import utc_now


class HistoricalImportRejected(DomainError):
    """A staged row does not describe an importable past session."""

    def __init__(self, message: str, code: str):
        super().__init__(message, error_code=code, http_status=422)


@dataclass(frozen=True)
class HistoricalSessionRecord:
    """One past session, as the source establishes it."""

    session_id: SessionId
    tenant_id: TenantId
    service_id: ServiceId
    provider_id: ProviderId
    client_id: ClientId
    delivered_at: datetime
    delivery_context: SessionDeliveryContext
    attendance: SessionAttendance = SessionAttendance.INDIVIDUAL
    member_id: EligibleMemberId | None = None
    provider_affiliation_id: str | None = None
    source_batch_id: str | None = None
    source_row_number: int | None = None
    # Activity-log values, normalised at staging; None where the source did not map.
    session_type: SessionType | None = None
    category: SessionCategory | None = None
    clinical_outcome: SessionClinicalStatus | None = None
    final_status: SessionStatus | None = None
    client_type: ClientType | None = None
    rate_ugx: int | None = None
    session_number: int | None = None
    # Enrichment: staging never blocks a row for lacking these.
    issue_topic: str | None = None
    diagnosis_type_id: str | None = None
    diagnosis_id: str | None = None
    approved_by: str | None = None


class RecordHistoricalSessionUseCase:
    """Record a past session without consulting present-day eligibility."""

    def __init__(
        self,
        session_repository: ServiceSessionRepository,
        provider_repository: ProviderRepository,
    ):
        self._sessions = session_repository
        self._providers = provider_repository
        # Scoped to one request, so it cannot go stale between them.
        self._provider_cache: dict[str, ProviderEntity | None] = {}

    async def execute(self, record: HistoricalSessionRecord) -> ServiceSessionEntity:
        await self._require_same_tenant_practitioner(record)
        _require_past(record.delivered_at)
        _require_consistent_context(record)
        _require_terminal_status(record.final_status)

        now = utc_now()
        session = ServiceSessionEntity(
            id=record.session_id,
            tenant_id=record.tenant_id,
            service_id=record.service_id,
            provider_id=record.provider_id,
            client_id=record.client_id,
            attendance=record.attendance,
            member_id=record.member_id,
            scheduled_at=record.delivered_at,
            delivery_context=record.delivery_context,
            provider_affiliation_id=record.provider_affiliation_id,
            # A no-show is the one historical outcome that is not a completion.
            status=record.final_status or SessionStatus.COMPLETED,
            completed_at=(
                record.delivered_at
                if (record.final_status or SessionStatus.COMPLETED) is SessionStatus.COMPLETED
                else None
            ),
            created_at=now,
            updated_at=now,
            reschedule_count=0,
            session_type=record.session_type,
            category=record.category,
            clinical_outcome=record.clinical_outcome,
            client_type=record.client_type,
            rate_ugx=record.rate_ugx,
            session_number=record.session_number,
            issue_topic=record.issue_topic,
            diagnosis_type_id=record.diagnosis_type_id,
            diagnosis_id=record.diagnosis_id,
            approved_by=record.approved_by,
        )
        await self._sessions.insert(session)
        return session

    async def _require_same_tenant_practitioner(self, record: HistoricalSessionRecord) -> None:
        """Resolved and same-tenant, but not required to be eligible today."""
        key = record.provider_id.value
        if key not in self._provider_cache:
            self._provider_cache[key] = await self._providers.get_by_id(record.provider_id)
        provider = self._provider_cache[key]
        if provider is None or provider.tenant_id != record.tenant_id:
            raise HistoricalImportRejected(
                f"Practitioner {record.provider_id.value} is not in this tenant",
                "practitioner_not_in_tenant",
            )


def _require_past(delivered_at: datetime) -> None:
    """A historical import cannot create a future booking."""
    if boundary_day(delivered_at) > boundary_day(utc_now()):
        raise HistoricalImportRejected(
            "A historical import cannot record a session dated in the future; "
            "book it through the ordinary path so eligibility applies",
            "future_session_through_import",
        )


def _require_consistent_context(record: HistoricalSessionRecord) -> None:
    """Organisation delivery carries an affiliation; the others carry none."""
    has_affiliation = record.provider_affiliation_id is not None
    if (record.delivery_context is SessionDeliveryContext.ORGANISATION) != has_affiliation:
        raise HistoricalImportRejected(
            "Organisation delivery requires an affiliation, and direct or unknown "
            "delivery must not carry one",
            "delivery_context_inconsistent",
        )


def _require_terminal_status(status: SessionStatus | None) -> None:
    """A past session either happened or nobody came; other states are live ones."""
    if status is not None and status not in (SessionStatus.COMPLETED, SessionStatus.NO_SHOW):
        raise HistoricalImportRejected(
            f"A historical session cannot be recorded as {status.value}",
            code="HISTORICAL_STATUS_NOT_TERMINAL",
        )
