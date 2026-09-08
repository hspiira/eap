"""Service category taxonomy model.

Reference data shared across tenants. ``code`` is the stable identity that
``services.category`` and ``authorizations.service_category`` reference by
foreign key; ``name`` and ``description`` are display labels, edited in
place, and every edit bumps ``version``. Retirement is dated: deactivating a
row sets ``effective_until``, and reactivating clears it, mirroring
``DiagnosisTypeModel``.
"""

from datetime import datetime

from sqlalchemy import Boolean, DateTime, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from app.infrastructure.models.base import Base, CuidMixin, TimestampMixin


class ServiceCategoryModel(CuidMixin, Base, TimestampMixin):
    """Coarse grouping used by EAP programme caps and authorization rules."""

    __tablename__ = "service_categories"

    code: Mapped[str] = mapped_column(String(50), unique=True, nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(String(2000), nullable=True)
    sort_order: Mapped[int] = mapped_column(Integer, nullable=False, server_default="0")
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default="true")
    version: Mapped[int] = mapped_column(Integer, nullable=False, server_default="1")
    effective_until: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
