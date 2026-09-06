"""Contract lifecycle transitions that compare dates.

DateRange holds `date` values while utc_now() returns a datetime. Archiving
a contract compared the two directly and raised TypeError, surfacing as a
500 from POST /contracts/{id}/archive.
"""

from datetime import UTC, datetime, timedelta
from decimal import Decimal

import pytest

from app.domain.entities.contract import ContractEntity
from app.domain.enums import ContractStatus, PaymentFrequency, PaymentStatus
from app.domain.value_objects.core import ClientId, ContractId, Money, TenantId
from app.domain.value_objects.dates import DateRange
from app.shared.utils.datetime import utc_now


def _contract(
    *,
    start_offset_days: int,
    end_offset_days: int,
    status: ContractStatus = ContractStatus.ACTIVE,
) -> ContractEntity:
    today = datetime.now(UTC).date()
    now = utc_now()
    return ContractEntity(
        id=ContractId("contract-1"),
        tenant_id=TenantId("tenant-1"),
        client_id=ClientId("client-1"),
        period=DateRange(
            start_date=today + timedelta(days=start_offset_days),
            end_date=today + timedelta(days=end_offset_days),
        ),
        billing_rate=Money(amount=Decimal("5000.00"), currency="USD"),
        payment_frequency=PaymentFrequency.MONTHLY,
        payment_status=PaymentStatus.PENDING,
        status=status,
        is_auto_renew=False,
        created_at=now,
        updated_at=now,
    )


class TestArchive:
    def test_archiving_a_current_contract_leaves_it_active(self):
        contract = _contract(start_offset_days=-30, end_offset_days=30)
        contract.archive()
        assert contract.status == ContractStatus.ACTIVE

    def test_archiving_an_expired_contract_marks_it_expired(self):
        contract = _contract(start_offset_days=-365, end_offset_days=-1)
        contract.archive()
        assert contract.status == ContractStatus.EXPIRED

    def test_archiving_a_contract_ending_today_leaves_it_active(self):
        contract = _contract(start_offset_days=-30, end_offset_days=0)
        contract.archive()
        assert contract.status == ContractStatus.ACTIVE

    def test_archiving_a_deleted_contract_is_rejected(self):
        contract = _contract(start_offset_days=-30, end_offset_days=30)
        contract.deleted_at = utc_now()
        with pytest.raises(Exception, match="deleted"):
            contract.archive()


class TestRestore:
    def test_restoring_an_expired_contract_within_its_period_reactivates_it(self):
        contract = _contract(
            start_offset_days=-30, end_offset_days=30, status=ContractStatus.EXPIRED
        )
        contract.restore()
        assert contract.status == ContractStatus.ACTIVE

    def test_restoring_a_contract_past_its_end_date_leaves_it_expired(self):
        contract = _contract(
            start_offset_days=-365, end_offset_days=-1, status=ContractStatus.EXPIRED
        )
        contract.restore()
        assert contract.status == ContractStatus.EXPIRED

    def test_restoring_an_active_contract_is_a_conflict(self):
        contract = _contract(start_offset_days=-30, end_offset_days=30)
        with pytest.raises(Exception, match="already active"):
            contract.restore()
