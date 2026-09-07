"""The adapter that turns an Accepted staged row into a past session.

Before resolution existed it refused every row. Now it converts what staging
resolved and still refuses rather than guesses when an Accepted row is missing
what the write path requires.
"""

from datetime import UTC, date, datetime
from unittest.mock import AsyncMock

import pytest

from app.application.services.historical_session_writer import HistoricalSessionWriterAdapter
from app.application.use_cases.apply_session_import import ImportRowNotConvertible
from app.domain.entities.session_import import SessionImportRowEntity
from app.domain.enums import (
    SessionAttendance,
    SessionCategory,
    SessionClinicalStatus,
    SessionStatus,
    SessionType,
)
from app.domain.enums.provider_network import DeliveryContext, ImportRowOutcome
from app.domain.value_objects.core import ProviderId, TenantId
from app.domain.value_objects.provider_network import SessionImportBatchId, SessionImportRowId

TENANT = TenantId("t-1")
NOW = datetime(2026, 9, 1, tzinfo=UTC)


def _row(**overrides) -> SessionImportRowEntity:
    defaults = {
        "id": SessionImportRowId("row-1"),
        "batch_id": SessionImportBatchId("batch-1"),
        "tenant_id": TENANT,
        "row_number": 7,
        "source_record_key": None,
        "raw_practitioner_name": "Moses Mpanga",
        "session_date": date(2025, 4, 2),
        "outcome": ImportRowOutcome.ACCEPTED,
        "created_at": NOW,
        "delivery_context": DeliveryContext.UNKNOWN,
        "provider_id": ProviderId("prov-1"),
        "client_id": "cli-1",
        "attendance": SessionAttendance.INDIVIDUAL,
        "member_id": "mem-1",
        "service_id": "svc-1",
        "session_type": SessionType.PHYSICAL,
        "category": SessionCategory.INDIVIDUAL,
        "clinical_outcome": SessionClinicalStatus.TO_BE_CONTINUED,
        "rate_ugx": 100000,
        "session_number": 3,
    }
    return SessionImportRowEntity(**{**defaults, **overrides})


def _adapter():
    use_case = AsyncMock()
    use_case.execute.return_value = type("S", (), {"id": type("I", (), {"value": "sess-1"})()})()
    return HistoricalSessionWriterAdapter(use_case), use_case


class TestConversion:
    async def test_an_accepted_row_becomes_a_historical_record(self):
        adapter, use_case = _adapter()

        session_id = await adapter.record(_row(), TENANT)

        assert session_id == "sess-1"
        record = use_case.execute.await_args.args[0]
        assert record.client_id.value == "cli-1"
        assert record.attendance is SessionAttendance.INDIVIDUAL
        assert record.member_id.value == "mem-1"
        assert record.category is SessionCategory.INDIVIDUAL
        assert record.clinical_outcome is SessionClinicalStatus.TO_BE_CONTINUED
        assert record.rate_ugx == 100000
        assert record.source_batch_id == "batch-1"

    async def test_a_company_wide_row_converts_with_no_member(self):
        adapter, use_case = _adapter()

        await adapter.record(
            _row(attendance=SessionAttendance.COMPANY_WIDE, member_id=None), TENANT
        )

        record = use_case.execute.await_args.args[0]
        assert record.attendance is SessionAttendance.COMPANY_WIDE
        assert record.member_id is None

    async def test_a_no_show_row_carries_the_scheduling_status(self):
        adapter, use_case = _adapter()

        await adapter.record(
            _row(clinical_outcome=None, session_status=SessionStatus.NO_SHOW), TENANT
        )

        assert use_case.execute.await_args.args[0].final_status is SessionStatus.NO_SHOW


class TestRefusals:
    """An Accepted row missing a requirement fails loudly, never silently."""

    # A missing practitioner is not parametrised here: the row entity itself
    # refuses to construct an Accepted row without one, so the adapter's guard
    # for it is unreachable through a valid entity.
    @pytest.mark.parametrize(
        ("overrides", "fragment"),
        [
            ({"client_id": None}, "client"),
            ({"service_id": None}, "service"),
            ({"member_id": None}, "member"),
        ],
    )
    async def test_a_missing_requirement_refuses_the_row(self, overrides, fragment):
        adapter, use_case = _adapter()

        with pytest.raises(ImportRowNotConvertible, match=fragment):
            await adapter.record(_row(**overrides), TENANT)

        use_case.execute.assert_not_awaited()
