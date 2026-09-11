"""Diagnosis taxonomy models (Phase 2 #D-Tax).

Reference data shared across tenants. Two-level hierarchy: ``DiagnosisType``
(category, e.g. "Mental Ill Health") groups ``Diagnosis`` rows (specific
condition, e.g. "Depression").

``code`` is the stable identity and never changes once sessions reference it.
``name`` and ``description`` are display labels, edited in place, and every
edit bumps ``version``. Retirement is dated: deactivating a row sets
``effective_until``, and reactivating clears it, so the two conditions the read
queries require always agree. Rows are not append-only, and a superseded label
is not recoverable from these tables; a rendered report keeps the label it was
built from in ``report_runs.output``.
"""

from datetime import datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.infrastructure.models.base import Base, CuidMixin, TenantMixin, TimestampMixin


class DiagnosisTypeModel(CuidMixin, Base, TimestampMixin):
    """Top-level category in the diagnosis taxonomy."""

    __tablename__ = "diagnosis_types"

    code: Mapped[str] = mapped_column(String(50), unique=True, nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    sort_order: Mapped[int] = mapped_column(Integer, nullable=False, server_default="0")
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default="true")
    version: Mapped[int] = mapped_column(Integer, nullable=False, server_default="1")
    effective_until: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    diagnoses: Mapped[list["DiagnosisModel"]] = relationship(
        "DiagnosisModel",
        back_populates="diagnosis_type",
        cascade="all, delete-orphan",
    )


class DiagnosisModel(CuidMixin, Base, TimestampMixin):
    """Specific diagnosis within a category."""

    __tablename__ = "diagnoses"

    type_id: Mapped[str] = mapped_column(
        ForeignKey("diagnosis_types.id"), nullable=False, index=True
    )
    code: Mapped[str] = mapped_column(String(50), unique=True, nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    sort_order: Mapped[int] = mapped_column(Integer, nullable=False, server_default="0")
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default="true")
    version: Mapped[int] = mapped_column(Integer, nullable=False, server_default="1")
    effective_until: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    diagnosis_type: Mapped["DiagnosisTypeModel"] = relationship(
        "DiagnosisTypeModel", back_populates="diagnoses"
    )


class TenantDiagnosisSettingModel(CuidMixin, TenantMixin, Base, TimestampMixin):
    """Per-tenant overlay on the shared taxonomy.

    The taxonomy itself stays global so prevalence remains comparable across
    tenants. A missing row means enabled at the taxonomy's own sort order.
    """

    __tablename__ = "tenant_diagnosis_settings"

    diagnosis_type_id: Mapped[str] = mapped_column(
        ForeignKey("diagnosis_types.id", ondelete="CASCADE"), nullable=False, index=True
    )
    diagnosis_id: Mapped[str | None] = mapped_column(
        ForeignKey("diagnoses.id", ondelete="CASCADE"), nullable=True, index=True
    )
    is_enabled: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default="true")
    sort_order: Mapped[int | None] = mapped_column(Integer, nullable=True)
    local_label: Mapped[str | None] = mapped_column(String(255), nullable=True)
