"""Utilisation event type taxonomy model.

Reference data shared across tenants. ``code`` is the stable identity that
``utilisation_events.event_type`` references by foreign key.
"""

from datetime import datetime

from sqlalchemy import Boolean, DateTime, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from app.infrastructure.models.base import Base, CuidMixin, TimestampMixin


class UtilisationEventTypeModel(CuidMixin, Base, TimestampMixin):
    __tablename__ = "utilisation_event_types"

    code: Mapped[str] = mapped_column(String(50), unique=True, nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(String(2000), nullable=True)
    sort_order: Mapped[int] = mapped_column(Integer, nullable=False, server_default="0")
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default="true")
    version: Mapped[int] = mapped_column(Integer, nullable=False, server_default="1")
    effective_until: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
