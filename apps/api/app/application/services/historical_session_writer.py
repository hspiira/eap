"""Adapter from a staged row to agent 1's historical write path.

Translation happens here rather than by importing their session enum into this
module's aggregate, as agreed. It also refuses rather than guesses: a row that
reached Accepted without the fields the write path requires fails loudly, so a
batch cannot report itself applied having silently dropped rows.
"""

from datetime import datetime, time

from app.application.use_cases.apply_session_import import ImportRowNotConvertible
from app.application.use_cases.historical_session_import import HistoricalSessionRecord
from app.domain.entities.session_import import SessionImportRowEntity
from app.domain.enums import SessionAttendance, SessionDeliveryContext
from app.domain.enums.provider_network import DeliveryContext
from app.domain.services.provider_network_calendar import PROVIDER_BOUNDARY_TIMEZONE
from app.domain.value_objects.core import (
    ClientId,
    EligibleMemberId,
    ProviderId,
    ServiceId,
    SessionId,
    TenantId,
)
from app.shared.utils.generators import generate_cuid

_CONTEXTS = {
    DeliveryContext.DIRECT: "Direct",
    DeliveryContext.ORGANISATION: "Organisation",
    DeliveryContext.UNKNOWN: "Unknown",
}


class HistoricalSessionWriterAdapter:
    def __init__(self, record_use_case):
        self._record = record_use_case

    async def record(self, row: SessionImportRowEntity, tenant_id: TenantId) -> str:
        """Write one past session and return its id.

        Refuses rather than guesses: an Accepted row missing what the write
        path requires fails loudly, so a batch cannot report itself applied
        having silently dropped rows.
        """
        if row.provider_id is None:
            raise ImportRowNotConvertible(row.row_number, "no resolved practitioner")
        if row.client_id is None or row.attendance is None:
            raise ImportRowNotConvertible(row.row_number, "no resolved client or attendance")
        if row.service_id is None:
            raise ImportRowNotConvertible(row.row_number, "no resolved service")
        if row.attendance is SessionAttendance.INDIVIDUAL and row.member_id is None:
            raise ImportRowNotConvertible(row.row_number, "individual row has no resolved member")

        record = HistoricalSessionRecord(
            session_id=SessionId(generate_cuid()),
            tenant_id=tenant_id,
            service_id=ServiceId(row.service_id),
            provider_id=ProviderId(row.provider_id.value),
            client_id=ClientId(row.client_id),
            attendance=row.attendance,
            member_id=EligibleMemberId(row.member_id) if row.member_id else None,
            delivered_at=self.delivered_at(row),
            delivery_context=SessionDeliveryContext(self.delivery_context(row)),
            provider_affiliation_id=(
                row.provider_affiliation_id.value if row.provider_affiliation_id else None
            ),
            source_batch_id=row.batch_id.value,
            source_row_number=row.row_number,
            session_type=row.session_type,
            category=row.category,
            clinical_outcome=row.clinical_outcome,
            final_status=row.session_status,
            client_type=row.client_type,
            rate_ugx=row.rate_ugx,
            session_number=row.session_number,
        )
        session = await self._record.execute(record)
        return session.id.value

    @staticmethod
    def delivered_at(row: SessionImportRowEntity) -> datetime:
        """Midday in the boundary timezone, so a date cannot slip a day."""
        if row.session_date is None:
            raise ImportRowNotConvertible(row.row_number, "no session date")
        return datetime.combine(row.session_date, time(12, 0), tzinfo=PROVIDER_BOUNDARY_TIMEZONE)

    @staticmethod
    def delivery_context(row: SessionImportRowEntity) -> str:
        return _CONTEXTS[row.delivery_context]
