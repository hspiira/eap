"""Pricing engine (Phase 2 #D-Pricing).

Computes an :class:`InvoicePreview` for a contract over a billing window. One
calculation path per :class:`PricingModel`. Pure domain logic — no DB, no I/O.
The application layer (route or use case) is responsible for loading the
contract and the relevant utilisation events.
"""

from __future__ import annotations

import decimal
from collections.abc import Sequence
from datetime import date

from app.domain.entities.contract import ContractEntity
from app.domain.entities.utilisation_event import UtilisationEventEntity
from app.domain.enums import PricingModel
from app.domain.exceptions import DomainError
from app.domain.value_objects.core import Money
from app.domain.value_objects.pricing import (
    ContractPricing,
    InvoiceLine,
    InvoicePreview,
)


class PricingEngine:
    """Computes invoice previews from contract pricing + utilisation events."""

    def compute(
        self,
        contract: ContractEntity,
        events: Sequence[UtilisationEventEntity],
        period_from: date,
        period_to: date,
    ) -> InvoicePreview:
        if contract.pricing is None:
            raise DomainError("Contract has no pricing configuration")
        pricing = contract.pricing
        events_in_window = [
            e for e in events if period_from <= e.occurred_on <= period_to
        ]
        if pricing.model == PricingModel.RETAINER:
            lines, notes = _retainer(pricing)
        elif pricing.model == PricingModel.FRAMEWORK:
            lines, notes = _framework(pricing, events_in_window)
        elif pricing.model == PricingModel.FEE_FOR_SERVICE:
            lines, notes = _fee_for_service(pricing, events_in_window)
        elif pricing.model == PricingModel.ADMIN_UTILISATION:
            lines, notes = _admin_utilisation(pricing, events_in_window)
        elif pricing.model == PricingModel.VALUE_ADD:
            lines, notes = _value_add(pricing)
        else:
            raise DomainError(f"Unsupported pricing model: {pricing.model}")
        currency = _currency_for(pricing)
        subtotal = _sum_lines(lines, currency)
        return InvoicePreview(
            contract_id=contract.id,
            period_from=period_from,
            period_to=period_to,
            pricing_model=pricing.model,
            currency=currency,
            lines=tuple(lines),
            subtotal=subtotal,
            notes=tuple(notes),
        )


def _retainer(pricing: ContractPricing) -> tuple[list[InvoiceLine], list[str]]:
    assert pricing.retainer_amount is not None
    line = InvoiceLine(
        description="Retainer fee",
        quantity=1,
        unit_amount=pricing.retainer_amount,
        total=pricing.retainer_amount,
    )
    return [line], []


def _framework(
    pricing: ContractPricing, events: Sequence[UtilisationEventEntity]
) -> tuple[list[InvoiceLine], list[str]]:
    assert pricing.deposit_amount is not None
    assert pricing.rate_card is not None
    lines: list[InvoiceLine] = []
    drawn_total = decimal.Decimal("0")
    for event in events:
        rate = _rate_for_event(pricing, event)
        if rate is None:
            continue
        total = rate.multiply(decimal.Decimal(event.units))
        drawn_total += total.amount
        lines.append(
            InvoiceLine(
                description=f"Drawdown — {event.event_type.value}"
                + (f" ({event.service_code})" if event.service_code else ""),
                quantity=event.units,
                unit_amount=rate,
                total=total,
            )
        )
    notes = [
        f"Framework deposit: {pricing.deposit_amount.amount} {pricing.deposit_amount.currency}",
        f"Period drawdown: {drawn_total} {pricing.deposit_amount.currency}",
        f"Remaining balance: {pricing.deposit_amount.amount - drawn_total} {pricing.deposit_amount.currency}",
    ]
    return lines, notes


def _fee_for_service(
    pricing: ContractPricing, events: Sequence[UtilisationEventEntity]
) -> tuple[list[InvoiceLine], list[str]]:
    assert pricing.rate_card is not None
    lines: list[InvoiceLine] = []
    for event in events:
        rate = _rate_for_event(pricing, event)
        if rate is None:
            continue
        total = rate.multiply(decimal.Decimal(event.units))
        lines.append(
            InvoiceLine(
                description=f"{event.event_type.value}"
                + (f" — {event.service_code}" if event.service_code else ""),
                quantity=event.units,
                unit_amount=rate,
                total=total,
            )
        )
    return lines, []


def _admin_utilisation(
    pricing: ContractPricing, events: Sequence[UtilisationEventEntity]
) -> tuple[list[InvoiceLine], list[str]]:
    assert pricing.admin_fee_floor is not None
    assert pricing.rate_card is not None
    floor_line = InvoiceLine(
        description="Admin fee (floor)",
        quantity=1,
        unit_amount=pricing.admin_fee_floor,
        total=pricing.admin_fee_floor,
    )
    usage_lines: list[InvoiceLine] = []
    for event in events:
        rate = _rate_for_event(pricing, event)
        if rate is None:
            continue
        total = rate.multiply(decimal.Decimal(event.units))
        usage_lines.append(
            InvoiceLine(
                description=f"Usage — {event.event_type.value}"
                + (f" ({event.service_code})" if event.service_code else ""),
                quantity=event.units,
                unit_amount=rate,
                total=total,
            )
        )
    return [floor_line, *usage_lines], []


def _value_add(pricing: ContractPricing) -> tuple[list[InvoiceLine], list[str]]:
    assert pricing.parent_contract_id is not None
    return [], [
        f"Value-Add bundling: charges roll up to parent contract {pricing.parent_contract_id.value}.",
    ]


def _rate_for_event(
    pricing: ContractPricing, event: UtilisationEventEntity
) -> Money | None:
    if pricing.rate_card is None or event.service_code is None:
        return None
    return pricing.rate_card.rate_for(event.service_code)


def _currency_for(pricing: ContractPricing) -> str:
    if pricing.retainer_amount is not None:
        return pricing.retainer_amount.currency
    if pricing.deposit_amount is not None:
        return pricing.deposit_amount.currency
    if pricing.admin_fee_floor is not None:
        return pricing.admin_fee_floor.currency
    if pricing.rate_card is not None:
        return pricing.rate_card.rates[0][1].currency
    return "UGX"


def _sum_lines(lines: Sequence[InvoiceLine], currency: str) -> Money:
    total = decimal.Decimal("0")
    for line in lines:
        total += line.total.amount
    return Money(amount=total, currency=currency)
