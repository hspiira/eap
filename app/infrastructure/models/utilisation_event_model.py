"""Utilisation event model (Phase 2 #D-Pricing)."""

from datetime import date

from sqlalchemy import Date, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.domain.enums import UtilisationEventType
from app.infrastructure.models.base import (
    Base,
    CuidMixin,
    EnumValueType,
    TenantMixin,
    TimestampMixin,
)


class UtilisationEventModel(CuidMixin, TenantMixin, Base, TimestampMixin):
    __tablename__ = "utilisation_events"

    contract_id: Mapped[str] = mapped_column(String(25), nullable=False, index=True)
    event_type: Mapped[UtilisationEventType] = mapped_column(
        EnumValueType(UtilisationEventType), nullable=False, index=True
    )
    occurred_on: Mapped[date] = mapped_column(Date, nullable=False, index=True)
    units: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    service_code: Mapped[str | None] = mapped_column(String(50), nullable=True, index=True)
    source_id: Mapped[str | None] = mapped_column(String(25), nullable=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
