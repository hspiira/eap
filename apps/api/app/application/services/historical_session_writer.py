"""Adapter from a staged row to agent 1's historical write path.

Translation happens here rather than by importing their session enum into this
module's aggregate, as agreed. It also refuses rather than guesses: a row that
reached Accepted without the fields the write path requires fails loudly, so a
batch cannot report itself applied having silently dropped rows.
"""

from datetime import datetime, time

from app.application.use_cases.apply_session_import import ImportRowNotConvertible
from app.domain.entities.session_import import SessionImportRowEntity
from app.domain.enums.provider_network import DeliveryContext
from app.domain.services.provider_network_calendar import PROVIDER_BOUNDARY_TIMEZONE
from app.domain.value_objects.core import TenantId

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

        Unreachable today: no staged row reaches Accepted, because the record
        below needs a member and a service and nothing resolves either yet.
        """
        raise ImportRowNotConvertible(
            row.row_number,
            "the historical write path requires a member and a service, and "
            "staging resolves neither; see the UnresolvedMember and "
            "UnresolvedService outcomes",
        )

    @staticmethod
    def delivered_at(row: SessionImportRowEntity) -> datetime:
        """Midday in the boundary timezone, so a date cannot slip a day."""
        if row.session_date is None:
            raise ImportRowNotConvertible(row.row_number, "no session date")
        return datetime.combine(row.session_date, time(12, 0), tzinfo=PROVIDER_BOUNDARY_TIMEZONE)

    @staticmethod
    def delivery_context(row: SessionImportRowEntity) -> str:
        return _CONTEXTS[row.delivery_context]
