"""Pricing value objects (Phase 2 #D-Pricing / SAD §5.2.3).

`ContractPricing` is the configuration the pricing engine consumes; one
shape per :class:`~app.domain.enums.PricingModel`. Concrete fields differ
per model so we use a discriminated value object; invalid combinations
raise on construction.
"""

from __future__ import annotations

import decimal
from dataclasses import dataclass, field
from datetime import date

from app.domain.enums import PricingModel
from app.domain.value_objects.core import ContractId, Money


@dataclass(frozen=True)
class RateCard:
    """Maps a service code to a per-unit rate."""

    rates: tuple[tuple[str, Money], ...]

    def __post_init__(self):
        if not self.rates:
            raise ValueError("RateCard must contain at least one rate entry")
        seen: set[str] = set()
        for code, _ in self.rates:
            if not code:
                raise ValueError("RateCard entry requires a service code")
            if code in seen:
                raise ValueError(f"Duplicate service code in RateCard: {code}")
            seen.add(code)

    def rate_for(self, service_code: str) -> Money | None:
        for code, rate in self.rates:
            if code == service_code:
                return rate
        return None


@dataclass(frozen=True)
class UtilisationTier:
    """Stepped pricing tier: usage above ``up_to_units`` switches rate."""

    up_to_units: int
    unit_rate: Money

    def __post_init__(self):
        if self.up_to_units <= 0:
            raise ValueError("UtilisationTier.up_to_units must be > 0")


@dataclass(frozen=True)
class ContractPricing:
    """Discriminated configuration block for a contract's pricing model.

    Required field per model:

    - ``RETAINER``: ``retainer_amount`` (single periodic charge per period).
    - ``FRAMEWORK``: ``deposit_amount`` (initial deposit) + ``rate_card``;
      drawdowns are computed against utilisation events.
    - ``FEE_FOR_SERVICE``: ``rate_card``.
    - ``ADMIN_UTILISATION``: ``admin_fee_floor`` + ``rate_card``; the floor
      is invoiced regardless of activity.
    - ``VALUE_ADD``: ``parent_contract_id`` (the broader Minet contract that
      absorbs the EAP cost, no per-EAP invoice line generated).
    """

    model: PricingModel
    retainer_amount: Money | None = None
    deposit_amount: Money | None = None
    admin_fee_floor: Money | None = None
    rate_card: RateCard | None = None
    parent_contract_id: ContractId | None = None
    tiers: tuple[UtilisationTier, ...] = field(default_factory=tuple)

    def __post_init__(self):
        if self.model == PricingModel.RETAINER and self.retainer_amount is None:
            raise ValueError("RETAINER pricing requires retainer_amount")
        if self.model == PricingModel.FRAMEWORK and (
            self.deposit_amount is None or self.rate_card is None
        ):
            raise ValueError("FRAMEWORK pricing requires deposit_amount and rate_card")
        if self.model == PricingModel.FEE_FOR_SERVICE and self.rate_card is None:
            raise ValueError("FEE_FOR_SERVICE pricing requires rate_card")
        if self.model == PricingModel.ADMIN_UTILISATION and (
            self.admin_fee_floor is None or self.rate_card is None
        ):
            raise ValueError("ADMIN_UTILISATION pricing requires admin_fee_floor and rate_card")
        if self.model == PricingModel.VALUE_ADD and self.parent_contract_id is None:
            raise ValueError("VALUE_ADD pricing requires parent_contract_id")


@dataclass(frozen=True)
class InvoiceLine:
    description: str
    quantity: int
    unit_amount: Money
    total: Money


@dataclass(frozen=True)
class InvoicePreview:
    """Materialised invoice projection for a single billing window."""

    contract_id: ContractId
    period_from: date
    period_to: date
    pricing_model: PricingModel
    currency: str
    lines: tuple[InvoiceLine, ...]
    subtotal: Money
    notes: tuple[str, ...] = field(default_factory=tuple)

    def __post_init__(self):
        if self.period_to < self.period_from:
            raise ValueError("period_to must be on or after period_from")
        for line in self.lines:
            if line.unit_amount.currency != self.currency:
                raise ValueError(
                    f"Line currency {line.unit_amount.currency} does not match invoice currency {self.currency}"
                )
        # subtotal sanity-check
        expected = decimal.Decimal("0")
        for line in self.lines:
            expected += line.total.amount
        if expected != self.subtotal.amount:
            raise ValueError(
                f"InvoicePreview.subtotal {self.subtotal.amount} does not match line total {expected}"
            )
