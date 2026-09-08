"""Pricing API schemas (Phase 2 #D-Pricing)."""

from __future__ import annotations

from datetime import date
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field

from app.domain.enums import PricingModel, UtilisationEventType


class MoneySchema(BaseModel):
    amount: Decimal
    currency: str = Field(..., min_length=3, max_length=3)


class RateCardEntrySchema(BaseModel):
    service_code: str
    rate: MoneySchema


class UtilisationTierSchema(BaseModel):
    up_to_units: int = Field(..., gt=0)
    unit_rate: MoneySchema


class ContractPricingSchema(BaseModel):
    model: PricingModel
    retainer_amount: MoneySchema | None = None
    deposit_amount: MoneySchema | None = None
    admin_fee_floor: MoneySchema | None = None
    rate_card: list[RateCardEntrySchema] | None = None
    parent_contract_id: str | None = None
    tiers: list[UtilisationTierSchema] = Field(default_factory=list)


class ContractPricingUpdate(BaseModel):
    pricing: ContractPricingSchema


class InvoiceLineResponse(BaseModel):
    description: str
    quantity: int
    unit_amount: MoneySchema
    total: MoneySchema


class InvoicePreviewResponse(BaseModel):
    contract_id: str
    period_from: date
    period_to: date
    pricing_model: PricingModel
    currency: str
    lines: list[InvoiceLineResponse]
    subtotal: MoneySchema
    notes: list[str]


class UtilisationEventCreate(BaseModel):
    contract_id: str
    event_type: UtilisationEventType
    occurred_on: date
    units: int = Field(default=1, gt=0)
    service_code: str | None = None
    source_id: str | None = None
    notes: str | None = None


class UtilisationEventResponse(BaseModel):
    id: str
    tenant_id: str
    contract_id: str
    event_type: UtilisationEventType
    occurred_on: date
    units: int
    service_code: str | None
    source_id: str | None
    notes: str | None

    model_config = ConfigDict(from_attributes=True)


class UtilisationEventListResponse(BaseModel):
    items: list[UtilisationEventResponse]
    total: int
    page: int
    limit: int
    has_more: bool
