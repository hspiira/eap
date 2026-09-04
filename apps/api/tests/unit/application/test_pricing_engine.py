"""Pricing engine scenario tests (Phase 2 #D-Pricing / SAD §5.2.3).

One scenario per :class:`PricingModel` covering the invoice-line shape,
subtotal arithmetic, and any model-specific notes.
"""

import decimal
from datetime import UTC, date, datetime

import pytest

from app.application.services.pricing_engine import PricingEngine
from app.domain.entities.contract import ContractEntity
from app.domain.entities.utilisation_event import UtilisationEventEntity
from app.domain.enums import (
    ContractStatus,
    PaymentFrequency,
    PaymentStatus,
    PricingModel,
    UtilisationEventType,
)
from app.domain.exceptions import DomainError
from app.domain.value_objects.core import (
    ClientId,
    ContractId,
    DateRange,
    Money,
    TenantId,
    UtilisationEventId,
)
from app.domain.value_objects.pricing import (
    ContractPricing,
    RateCard,
)


def _money(value: str, currency: str = "UGX") -> Money:
    return Money(amount=decimal.Decimal(value), currency=currency)


def _contract(pricing: ContractPricing) -> ContractEntity:
    now = datetime.now(UTC)
    period = DateRange(start_date=date(2026, 1, 1), end_date=date(2026, 12, 31))
    return ContractEntity(
        id=ContractId("c-1"),
        tenant_id=TenantId("t-1"),
        client_id=ClientId("client-1"),
        period=period,
        billing_rate=_money("0"),
        payment_frequency=PaymentFrequency.MONTHLY,
        payment_status=PaymentStatus.PENDING,
        status=ContractStatus.ACTIVE,
        is_auto_renew=False,
        created_at=now,
        updated_at=now,
        pricing=pricing,
    )


def _event(
    *,
    service_code: str = "INDIVIDUAL_COUNSELLING",
    units: int = 1,
    on: date = date(2026, 6, 15),
    event_type: UtilisationEventType = UtilisationEventType.SESSION_DELIVERED,
) -> UtilisationEventEntity:
    now = datetime.now(UTC)
    return UtilisationEventEntity(
        id=UtilisationEventId("u-1"),
        tenant_id=TenantId("t-1"),
        contract_id=ContractId("c-1"),
        event_type=event_type,
        occurred_on=on,
        units=units,
        service_code=service_code,
        source_id=None,
        notes=None,
        created_at=now,
        updated_at=now,
    )


PERIOD_FROM = date(2026, 6, 1)
PERIOD_TO = date(2026, 6, 30)


def test_retainer_emits_single_line():
    pricing = ContractPricing(
        model=PricingModel.RETAINER,
        retainer_amount=_money("1500000"),
    )
    preview = PricingEngine().compute(_contract(pricing), [], PERIOD_FROM, PERIOD_TO)
    assert preview.pricing_model == PricingModel.RETAINER
    assert len(preview.lines) == 1
    assert preview.lines[0].quantity == 1
    assert preview.lines[0].total.amount == decimal.Decimal("1500000")
    assert preview.subtotal.amount == decimal.Decimal("1500000")


def test_framework_drawdown_lines_and_balance_note():
    rate_card = RateCard(rates=(("INDIVIDUAL_COUNSELLING", _money("60000")),))
    pricing = ContractPricing(
        model=PricingModel.FRAMEWORK,
        deposit_amount=_money("3000000"),
        rate_card=rate_card,
    )
    events = [
        _event(units=2),
        _event(service_code="GROUP_COUNSELLING"),  # not on rate card → skipped
    ]
    preview = PricingEngine().compute(_contract(pricing), events, PERIOD_FROM, PERIOD_TO)
    assert len(preview.lines) == 1
    assert preview.lines[0].quantity == 2
    assert preview.lines[0].total.amount == decimal.Decimal("120000")
    assert preview.subtotal.amount == decimal.Decimal("120000")
    assert any("Framework deposit" in n for n in preview.notes)
    assert any("Remaining balance" in n for n in preview.notes)


def test_fee_for_service_one_line_per_event():
    rate_card = RateCard(
        rates=(
            ("INDIVIDUAL_COUNSELLING", _money("60000")),
            ("GROUP_COUNSELLING", _money("250000")),
        )
    )
    pricing = ContractPricing(model=PricingModel.FEE_FOR_SERVICE, rate_card=rate_card)
    events = [
        _event(service_code="INDIVIDUAL_COUNSELLING", units=4),
        _event(service_code="GROUP_COUNSELLING"),
    ]
    preview = PricingEngine().compute(_contract(pricing), events, PERIOD_FROM, PERIOD_TO)
    assert len(preview.lines) == 2
    assert preview.subtotal.amount == decimal.Decimal("4") * decimal.Decimal(
        "60000"
    ) + decimal.Decimal("250000")


def test_admin_utilisation_floor_plus_usage():
    rate_card = RateCard(rates=(("INDIVIDUAL_COUNSELLING", _money("60000")),))
    pricing = ContractPricing(
        model=PricingModel.ADMIN_UTILISATION,
        admin_fee_floor=_money("500000"),
        rate_card=rate_card,
    )
    events = [_event(units=3)]
    preview = PricingEngine().compute(_contract(pricing), events, PERIOD_FROM, PERIOD_TO)
    assert len(preview.lines) == 2  # floor + usage
    assert preview.lines[0].description == "Admin fee (floor)"
    assert preview.lines[0].total.amount == decimal.Decimal("500000")
    assert preview.lines[1].quantity == 3
    assert preview.subtotal.amount == decimal.Decimal("680000")


def test_value_add_emits_no_lines_just_a_note():
    pricing = ContractPricing(
        model=PricingModel.VALUE_ADD,
        parent_contract_id=ContractId("parent-1"),
    )
    preview = PricingEngine().compute(_contract(pricing), [], PERIOD_FROM, PERIOD_TO)
    assert preview.lines == ()
    assert preview.subtotal.amount == decimal.Decimal("0")
    assert any("parent-1" in n for n in preview.notes)


def test_events_outside_window_are_ignored():
    rate_card = RateCard(rates=(("INDIVIDUAL_COUNSELLING", _money("60000")),))
    pricing = ContractPricing(model=PricingModel.FEE_FOR_SERVICE, rate_card=rate_card)
    events = [
        _event(on=date(2026, 5, 31)),  # before window
        _event(on=date(2026, 6, 15)),  # in window
        _event(on=date(2026, 7, 1)),  # after window
    ]
    preview = PricingEngine().compute(_contract(pricing), events, PERIOD_FROM, PERIOD_TO)
    assert len(preview.lines) == 1


def test_missing_pricing_raises():
    contract = _contract(ContractPricing(model=PricingModel.RETAINER, retainer_amount=_money("1")))
    contract.pricing = None
    with pytest.raises(DomainError):
        PricingEngine().compute(contract, [], PERIOD_FROM, PERIOD_TO)


def test_pricing_config_validation_retainer_requires_amount():
    with pytest.raises(ValueError):
        ContractPricing(model=PricingModel.RETAINER)


def test_pricing_config_validation_framework_requires_deposit_and_rate_card():
    with pytest.raises(ValueError):
        ContractPricing(model=PricingModel.FRAMEWORK)


def test_pricing_config_validation_value_add_requires_parent():
    with pytest.raises(ValueError):
        ContractPricing(model=PricingModel.VALUE_ADD)
