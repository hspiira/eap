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

from app.domain.entities.service_session import ServiceSessionEntity
from app.domain.enums import SessionDeliveryContext, SessionStatus
from app.domain.exceptions import DomainError
from app.domain.repositories.provider_repository import ProviderRepository
from app.domain.repositories.service_session_repository import ServiceSessionRepository
from app.domain.services.provider_network_calendar import boundary_day
from app.domain.value_objects.core import (
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
    member_id: EligibleMemberId
    delivered_at: datetime
    delivery_context: SessionDeliveryContext
    provider_affiliation_id: str | None = None
    source_batch_id: str | None = None
    source_row_number: int | None = None


class RecordHistoricalSessionUseCase:
    """Record a past session without consulting present-day eligibility."""

    def __init__(
        self,
        session_repository: ServiceSessionRepository,
        provider_repository: ProviderRepository,
    ):
        self._sessions = session_repository
        self._providers = provider_repository

    async def execute(self, record: HistoricalSessionRecord) -> ServiceSessionEntity:
        await self._require_same_tenant_practitioner(record)
        _require_past(record.delivered_at)
        _require_consistent_context(record)

        now = utc_now()
        session = ServiceSessionEntity(
            id=record.session_id,
            tenant_id=record.tenant_id,
            service_id=record.service_id,
            provider_id=record.provider_id,
            member_id=record.member_id,
            scheduled_at=record.delivered_at,
            delivery_context=record.delivery_context,
            provider_affiliation_id=record.provider_affiliation_id,
            status=SessionStatus.COMPLETED,
            completed_at=record.delivered_at,
            created_at=now,
            updated_at=now,
            reschedule_count=0,
        )
        await self._sessions.save(session)
        return session

    async def _require_same_tenant_practitioner(self, record: HistoricalSessionRecord) -> None:
        """Resolved and same-tenant, but not required to be eligible today."""
        provider = await self._providers.get_by_id(record.provider_id)
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
