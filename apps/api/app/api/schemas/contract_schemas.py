"""
Contract API Schemas (DTOs)

Pydantic models for request/response validation.
Separate from domain entities.
"""

from datetime import date, datetime

from pydantic import BaseModel, ConfigDict, Field

from app.api.schemas.base import SanitizedStr
from app.domain.enums import ContractStatus, PaymentFrequency, PaymentStatus, PricingModel

# === Value Object Schemas ===


class MoneySchema(BaseModel):
    """Money value object schema for request/response."""

    amount: str = Field(..., description="Amount as decimal string")
    currency: str = Field(..., min_length=3, max_length=3, description="ISO 3-letter currency code")


class DateRangeSchema(BaseModel):
    """Date range schema."""

    start_date: date = Field(..., description="Start date")
    end_date: date = Field(..., description="End date")


# === Request Schemas ===


class MoneyCreate(BaseModel):
    """Money for creation."""

    amount: str = Field(..., description="Amount as decimal string")
    currency: str = Field(..., min_length=3, max_length=3, description="ISO 3-letter currency code")


class ContractCreate(BaseModel):
    """Request schema for creating a contract."""

    client_id: str = Field(..., description="Client identifier")
    start_date: date = Field(..., description="Contract start date")
    end_date: date = Field(..., description="Contract end date")
    billing_rate: MoneySchema = Field(..., description="Billing rate")
    payment_frequency: PaymentFrequency = Field(..., description="Payment frequency")
    is_auto_renew: bool = Field(False, description="Whether contract auto-renews")


class ContractRenewRequest(BaseModel):
    """Request schema for renewing a contract."""

    new_end_date: date = Field(..., description="End date of the new term")
    new_rate: MoneyCreate | None = Field(None, description="New billing rate (optional)")
    reference: SanitizedStr | None = Field(None, description="Reference for the new term")


class ContractTerminateRequest(BaseModel):
    """Request schema for terminating a contract."""

    reason: SanitizedStr = Field(..., min_length=1, description="Termination reason")


class ContractSignRequest(BaseModel):
    """Request schema for signing a contract."""

    signed_by: SanitizedStr = Field(..., min_length=1, description="Name of person signing")


class ContractUpdate(BaseModel):
    """Request schema for updating contract basic information."""

    billing_rate: MoneyCreate | None = Field(None, description="New billing rate")
    payment_frequency: PaymentFrequency | None = Field(None, description="New payment frequency")
    is_auto_renew: bool | None = Field(None, description="Auto-renew setting")


class ContractUpdatePaymentStatus(BaseModel):
    """Request schema for updating payment status."""

    payment_status: PaymentStatus = Field(..., description="New payment status")


# === Response Schemas ===


class ContractResponse(BaseModel):
    """Response schema for contract."""

    id: str = Field(..., description="Contract identifier")
    tenant_id: str = Field(..., description="Tenant identifier")
    client_id: str = Field(..., description="Client identifier")
    reference: str | None = Field(None, description="Human reference for the term")
    renewed_from_id: str | None = Field(None, description="The term this one renewed")
    period: DateRangeSchema = Field(..., description="Contract period")
    billing_rate: MoneySchema | None = Field(
        None,
        description=(
            "The standing charge, read from the contract's pricing. Absent on a "
            "model priced only by rate card, where no single figure stands for it."
        ),
    )
    pricing_model: PricingModel | None = Field(None, description="How this contract is priced")
    payment_frequency: PaymentFrequency = Field(..., description="Payment frequency")
    payment_status: PaymentStatus = Field(..., description="Payment status")
    status: ContractStatus = Field(
        ...,
        description=(
            "Status as at today. A term past its end date reads Expired whether or "
            "not anybody wrote that down."
        ),
    )
    recorded_status: ContractStatus = Field(
        ..., description="The status stored on the row, before the lapse is derived"
    )
    is_auto_renew: bool = Field(..., description="Whether contract auto-renews")
    last_billing_date: date | None = Field(None, description="Last billing date")
    next_billing_date: date | None = Field(None, description="Next billing date")
    signed_by: str | None = Field(None, description="Name of person who signed")
    signed_at: datetime | None = Field(None, description="When contract was signed")
    termination_reason: str | None = Field(None, description="Termination reason")
    is_active: bool = Field(..., description="Whether contract is currently active")
    days_remaining: int = Field(..., description="Days remaining in contract")

    model_config = ConfigDict(from_attributes=True)


class ContractMetricsItem(BaseModel):
    """What one contract term covers, and what it has cost so far."""

    contract_id: str = Field(..., description="Contract identifier")
    services: int = Field(..., description="Services assigned to the contract")
    sessions: int = Field(..., description="Completed sessions inside the term")
    sessions_priced: int = Field(..., description="How many of those carry a rate")
    spent: MoneySchema = Field(..., description="Sum of the rates on those sessions")


class ContractMetricsResponse(BaseModel):
    """Per-term coverage and spend for every contract a client holds."""

    client_id: str = Field(..., description="Client identifier")
    items: list[ContractMetricsItem] = Field(..., description="One entry per contract")


class ContractListResponse(BaseModel):
    """Response schema for contract list."""

    items: list[ContractResponse] = Field(..., description="List of contracts")
    total: int = Field(..., description="Total number of contracts matching filters")
    page: int = Field(..., description="Current page number")
    limit: int = Field(..., description="Items per page")
    has_more: bool = Field(..., description="Whether there are more items")
