"""
Contract Mapper

Converts between ContractEntity (domain) and ContractModel (persistence).
"""

import decimal

from app.domain.entities.contract import ContractEntity
from app.domain.enums import (
    ContractStatus,
    PaymentFrequency,
    PaymentStatus,
    PricingModel,
)
from app.domain.value_objects.core import (
    ClientId,
    ContractId,
    DateRange,
    Money,
    TenantId,
)
from app.domain.value_objects.pricing import (
    ContractPricing,
    RateCard,
    UtilisationTier,
)
from app.infrastructure.models.contract_model import ContractModel
from app.shared.utils.datetime import ensure_utc


def _money_from_dict(value: dict | None) -> Money | None:
    if value is None:
        return None
    return Money(
        amount=decimal.Decimal(str(value["amount"])),
        currency=value["currency"],
    )


def _money_to_dict(value: Money | None) -> dict | None:
    if value is None:
        return None
    return {"amount": str(value.amount), "currency": value.currency}


def _pricing_from_dict(data: dict | None) -> ContractPricing | None:
    if not data:
        return None
    rate_card_data = data.get("rate_card")
    rate_card = None
    if rate_card_data:
        rate_card = RateCard(
            rates=tuple(
                (entry["service_code"], _money_from_dict(entry["rate"])) for entry in rate_card_data
            ),
        )
    tiers_data = data.get("tiers") or []
    tiers = tuple(
        UtilisationTier(
            up_to_units=int(t["up_to_units"]),
            unit_rate=_money_from_dict(t["unit_rate"]),
        )
        for t in tiers_data
    )
    parent_contract_id = data.get("parent_contract_id")
    return ContractPricing(
        model=PricingModel(data["model"]),
        retainer_amount=_money_from_dict(data.get("retainer_amount")),
        deposit_amount=_money_from_dict(data.get("deposit_amount")),
        admin_fee_floor=_money_from_dict(data.get("admin_fee_floor")),
        rate_card=rate_card,
        parent_contract_id=ContractId(parent_contract_id) if parent_contract_id else None,
        tiers=tiers,
    )


def _pricing_to_dict(pricing: ContractPricing | None) -> dict | None:
    if pricing is None:
        return None
    rate_card_payload = None
    if pricing.rate_card is not None:
        rate_card_payload = [
            {"service_code": code, "rate": _money_to_dict(rate)}
            for code, rate in pricing.rate_card.rates
        ]
    tiers_payload = [
        {"up_to_units": tier.up_to_units, "unit_rate": _money_to_dict(tier.unit_rate)}
        for tier in pricing.tiers
    ]
    return {
        "model": pricing.model.value,
        "retainer_amount": _money_to_dict(pricing.retainer_amount),
        "deposit_amount": _money_to_dict(pricing.deposit_amount),
        "admin_fee_floor": _money_to_dict(pricing.admin_fee_floor),
        "rate_card": rate_card_payload,
        "parent_contract_id": pricing.parent_contract_id.value
        if pricing.parent_contract_id
        else None,
        "tiers": tiers_payload,
    }


class ContractMapper:
    """Mapper for ContractEntity ↔ ContractModel conversion"""

    @staticmethod
    def to_entity(model: ContractModel) -> ContractEntity:
        """
        Convert database model to domain entity.

        Args:
            model: ContractModel from database

        Returns:
            ContractEntity with business logic
        """
        # Reconstruct value objects
        contract_id = ContractId(model.id)
        tenant_id = TenantId(model.tenant_id)
        client_id = ClientId(model.client_id)

        # The term is two columns on the row; the domain models it as one DateRange.
        if model.start_date is None or model.end_date is None:
            raise ValueError("Contract period must have start_date and end_date")
        period = DateRange(
            start_date=ensure_utc(model.start_date),
            end_date=ensure_utc(model.end_date),
        )

        # Reconstruct Money from JSON
        billing_dict = model.billing_rate if isinstance(model.billing_rate, dict) else {}
        amount_value = billing_dict.get("amount")
        # Convert string to Decimal if needed
        if isinstance(amount_value, str):
            amount = decimal.Decimal(amount_value)
        else:
            amount = decimal.Decimal(str(amount_value)) if amount_value else decimal.Decimal("0")

        billing_rate = Money(
            amount=amount,
            currency=billing_dict["currency"],
        )

        # Reconstruct enums
        payment_frequency = PaymentFrequency(model.payment_frequency)
        payment_status = PaymentStatus(model.payment_status)
        status = ContractStatus(model.status)

        pricing = _pricing_from_dict(getattr(model, "pricing_config", None))

        return ContractEntity(
            id=contract_id,
            tenant_id=tenant_id,
            client_id=client_id,
            period=period,
            billing_rate=billing_rate,
            payment_frequency=payment_frequency,
            payment_status=payment_status,
            status=status,
            is_auto_renew=model.is_auto_renew,
            last_billing_date=model.last_billing_date,
            next_billing_date=model.next_billing_date,
            signed_by=model.signed_by,
            signed_at=ensure_utc(model.signed_at) if model.signed_at else None,
            termination_reason=model.termination_reason,
            pricing=pricing,
            created_at=ensure_utc(model.created_at),
            updated_at=ensure_utc(model.updated_at),
            deleted_at=ensure_utc(model.deleted_at) if model.deleted_at else None,
        )

    @staticmethod
    def to_model(entity: ContractEntity) -> ContractModel:
        """
        Convert domain entity to database model.

        Args:
            entity: ContractEntity with business logic

        Returns:
            ContractModel for persistence
        """
        # Serialize Money to JSON
        billing_dict = {
            "amount": str(entity.billing_rate.amount),
            "currency": entity.billing_rate.currency,
        }

        pricing_dict = _pricing_to_dict(entity.pricing)
        return ContractModel(
            id=entity.id.value,
            tenant_id=entity.tenant_id.value,
            client_id=entity.client_id.value,
            start_date=entity.period.start_date,
            end_date=entity.period.end_date,
            billing_rate=billing_dict,
            payment_frequency=entity.payment_frequency,
            payment_status=entity.payment_status,
            status=entity.status,
            is_auto_renew=entity.is_auto_renew,
            last_billing_date=entity.last_billing_date,
            next_billing_date=entity.next_billing_date,
            signed_by=entity.signed_by,
            signed_at=ensure_utc(entity.signed_at) if entity.signed_at else None,
            termination_reason=entity.termination_reason,
            pricing_model=entity.pricing.model.value if entity.pricing else None,
            pricing_config=pricing_dict,
            created_at=ensure_utc(entity.created_at),
            updated_at=ensure_utc(entity.updated_at),
            deleted_at=ensure_utc(entity.deleted_at) if entity.deleted_at else None,
        )
