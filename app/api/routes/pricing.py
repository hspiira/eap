"""Pricing routes (Phase 2 #D-Pricing).

Three endpoints:
- ``PATCH /contracts/{id}/pricing`` — set or replace pricing config.
- ``GET  /contracts/{id}/invoice-preview`` — compute an invoice line set.
- ``POST /utilisation-events`` — record a billable activity.
"""

from __future__ import annotations

import decimal
from datetime import date

from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import (
    get_audit_event_handler,
    get_contract_repository,
    get_utilisation_event_repository,
)
from app.api.schemas.pricing_schemas import (
    ContractPricingSchema,
    ContractPricingUpdate,
    InvoiceLineResponse,
    InvoicePreviewResponse,
    MoneySchema,
    UtilisationEventCreate,
    UtilisationEventResponse,
)
from app.application.services.pricing_engine import PricingEngine
from app.core.authorization import require_same_tenant
from app.core.database import get_db
from app.core.security import TokenData, get_current_user
from app.domain.entities.utilisation_event import UtilisationEventEntity
from app.domain.repositories.contract_repository import ContractRepository
from app.domain.repositories.utilisation_event_repository import (
    UtilisationEventRepository,
)
from app.domain.value_objects.core import (
    ContractId,
    Money,
    TenantId,
    UtilisationEventId,
)
from app.domain.value_objects.pricing import (
    ContractPricing,
    RateCard,
    UtilisationTier,
)
from app.shared.decorators import readonly, transactional
from app.shared.utils.datetime import utc_now
from app.shared.utils.generators import generate_cuid
from app.shared.utils.route_audit_helper import audit_entity_operation

router = APIRouter(tags=["pricing"])


def _money_from_schema(s: MoneySchema | None) -> Money | None:
    if s is None:
        return None
    return Money(amount=decimal.Decimal(s.amount), currency=s.currency)


def _money_to_schema(m: Money) -> MoneySchema:
    return MoneySchema(amount=m.amount, currency=m.currency)


def _pricing_from_schema(s: ContractPricingSchema) -> ContractPricing:
    rate_card = None
    if s.rate_card:
        rate_card = RateCard(
            rates=tuple(
                (entry.service_code, _money_from_schema(entry.rate))
                for entry in s.rate_card
            ),
        )
    tiers = tuple(
        UtilisationTier(
            up_to_units=t.up_to_units, unit_rate=_money_from_schema(t.unit_rate)
        )
        for t in s.tiers
    )
    return ContractPricing(
        model=s.model,
        retainer_amount=_money_from_schema(s.retainer_amount),
        deposit_amount=_money_from_schema(s.deposit_amount),
        admin_fee_floor=_money_from_schema(s.admin_fee_floor),
        rate_card=rate_card,
        parent_contract_id=ContractId(s.parent_contract_id)
        if s.parent_contract_id
        else None,
        tiers=tiers,
    )


@router.patch(
    "/contracts/{contract_id}/pricing",
    summary="Set or replace contract pricing configuration",
)
@transactional()
async def update_contract_pricing(
    contract_id: str,
    body: ContractPricingUpdate,
    request: Request,
    current_user: TokenData = Depends(get_current_user),
    contract_repo: ContractRepository = Depends(get_contract_repository),
    audit_handler=Depends(get_audit_event_handler),
    db: AsyncSession = Depends(get_db),
):
    contract = await contract_repo.get_by_id(ContractId(contract_id))
    if contract is None:
        raise HTTPException(status_code=404, detail="Contract not found")
    contract.update_pricing(_pricing_from_schema(body.pricing))
    await contract_repo.save(contract)
    await audit_entity_operation(
        entity=contract,
        audit_handler=audit_handler,
        tenant_id=contract.tenant_id,
        user_id=current_user.user_id,
        request=request,
    )
    return {"contract_id": contract.id.value, "pricing_model": contract.pricing.model.value}


@router.get(
    "/contracts/{contract_id}/invoice-preview",
    response_model=InvoicePreviewResponse,
    summary="Compute an invoice preview for a billing window",
)
@readonly()
async def invoice_preview(
    contract_id: str,
    period_from: date = Query(..., description="Period start date (inclusive)"),
    period_to: date = Query(..., description="Period end date (inclusive)"),
    _user: TokenData = Depends(get_current_user),
    contract_repo: ContractRepository = Depends(get_contract_repository),
    utilisation_repo: UtilisationEventRepository = Depends(
        get_utilisation_event_repository
    ),
    db: AsyncSession = Depends(get_db),
):
    contract = await contract_repo.get_by_id(ContractId(contract_id))
    if contract is None:
        raise HTTPException(status_code=404, detail="Contract not found")
    if contract.pricing is None:
        raise HTTPException(
            status_code=400, detail="Contract has no pricing configuration"
        )
    events = await utilisation_repo.list_for_contract(
        contract.tenant_id,
        contract.id,
        from_date=period_from,
        to_date=period_to,
    )
    preview = PricingEngine().compute(contract, events, period_from, period_to)
    return InvoicePreviewResponse(
        contract_id=preview.contract_id.value,
        period_from=preview.period_from,
        period_to=preview.period_to,
        pricing_model=preview.pricing_model,
        currency=preview.currency,
        lines=[
            InvoiceLineResponse(
                description=line.description,
                quantity=line.quantity,
                unit_amount=_money_to_schema(line.unit_amount),
                total=_money_to_schema(line.total),
            )
            for line in preview.lines
        ],
        subtotal=_money_to_schema(preview.subtotal),
        notes=list(preview.notes),
    )


@router.post(
    "/utilisation-events",
    response_model=UtilisationEventResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Record a billable activity against a contract",
)
@transactional()
async def create_utilisation_event(
    data: UtilisationEventCreate,
    request: Request,
    tenant_id: str = Query(..., description="Tenant identifier"),
    current_user: TokenData = Depends(require_same_tenant),
    repo: UtilisationEventRepository = Depends(get_utilisation_event_repository),
    audit_handler=Depends(get_audit_event_handler),
    db: AsyncSession = Depends(get_db),
):
    now = utc_now()
    event = UtilisationEventEntity(
        id=UtilisationEventId(generate_cuid()),
        tenant_id=TenantId(tenant_id),
        contract_id=ContractId(data.contract_id),
        event_type=data.event_type,
        occurred_on=data.occurred_on,
        units=data.units,
        service_code=data.service_code,
        source_id=data.source_id,
        notes=data.notes,
        created_at=now,
        updated_at=now,
    )
    await repo.save(event)
    await audit_entity_operation(
        entity=event,
        audit_handler=audit_handler,
        tenant_id=event.tenant_id,
        user_id=current_user.user_id,
        request=request,
    )
    return UtilisationEventResponse(
        id=event.id.value,
        tenant_id=event.tenant_id.value,
        contract_id=event.contract_id.value,
        event_type=event.event_type,
        occurred_on=event.occurred_on,
        units=event.units,
        service_code=event.service_code,
        source_id=event.source_id,
        notes=event.notes,
    )
