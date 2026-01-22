"""
Contract Mapper

Converts between ContractEntity (domain) and ContractModel (persistence).
"""

import decimal
from datetime import date, datetime

from app.domain.entities.contract import ContractEntity
from app.domain.enums import ContractStatus, PaymentFrequency, PaymentStatus
from app.domain.value_objects.core import (
    ClientId,
    ContractId,
    DateRange,
    Money,
    TenantId,
)
from app.infrastructure.models.contract_model import ContractModel
from app.shared.utils.datetime import ensure_utc


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

        # Reconstruct DateRange from JSON
        period_dict = model.period if isinstance(model.period, dict) else {}
        start_date_str = period_dict.get("start_date")
        end_date_str = period_dict.get("end_date")
        
        if start_date_str and end_date_str:
            # Parse ISO format datetime strings
            if isinstance(start_date_str, str):
                start_dt = datetime.fromisoformat(start_date_str.replace("Z", "+00:00"))
            else:
                start_dt = start_date_str
            if isinstance(end_date_str, str):
                end_dt = datetime.fromisoformat(end_date_str.replace("Z", "+00:00"))
            else:
                end_dt = end_date_str
            
            period = DateRange(
                start_date=ensure_utc(start_dt),
                end_date=ensure_utc(end_dt),
            )
        else:
            raise ValueError("Contract period must have start_date and end_date")

        # Reconstruct Money from JSON
        billing_dict = (
            model.billing_rate if isinstance(model.billing_rate, dict) else {}
        )
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

        # Create entity
        return ContractEntity(
            _id=contract_id,
            _tenant_id=tenant_id,
            _client_id=client_id,
            _period=period,
            _billing_rate=billing_rate,
            _payment_frequency=payment_frequency,
            _payment_status=payment_status,
            _status=status,
            _is_auto_renew=model.is_auto_renew,
            _last_billing_date=model.last_billing_date,
            _next_billing_date=model.next_billing_date,
            _signed_by=model.signed_by,
            _signed_at=ensure_utc(model.signed_at) if model.signed_at else None,
            _termination_reason=model.termination_reason,
            _created_at=ensure_utc(model.created_at),
            _updated_at=ensure_utc(model.updated_at),
            _deleted_at=ensure_utc(model.deleted_at) if model.deleted_at else None,
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
        # Serialize DateRange to JSON
        period_dict = {
            "start_date": entity._period.start_date.isoformat(),
            "end_date": entity._period.end_date.isoformat(),
        }

        # Serialize Money to JSON
        billing_dict = {
            "amount": str(entity._billing_rate.amount),
            "currency": entity._billing_rate.currency,
        }

        # Create model
        return ContractModel(
            id=entity._id.value,
            tenant_id=entity._tenant_id.value,
            client_id=entity._client_id.value,
            period=period_dict,
            billing_rate=billing_dict,
            payment_frequency=entity._payment_frequency,
            payment_status=entity._payment_status,
            status=entity._status,
            is_auto_renew=entity._is_auto_renew,
            last_billing_date=entity._last_billing_date,
            next_billing_date=entity._next_billing_date,
            signed_by=entity._signed_by,
            signed_at=ensure_utc(entity._signed_at) if entity._signed_at else None,
            termination_reason=entity._termination_reason,
            created_at=ensure_utc(entity._created_at),
            updated_at=ensure_utc(entity._updated_at),
            deleted_at=ensure_utc(entity._deleted_at) if entity._deleted_at else None,
        )
