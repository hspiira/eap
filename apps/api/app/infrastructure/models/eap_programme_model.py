"""EAP programme + Authorization models."""

from datetime import date, datetime

from sqlalchemy import Date, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.domain.enums import AuthorizationStatus
from app.infrastructure.models.base import (
    Base,
    CuidMixin,
    EnumValueType,
    TenantMixin,
    TimestampMixin,
)


class EAPProgrammeModel(CuidMixin, TenantMixin, Base, TimestampMixin):
    __tablename__ = "eap_programmes"

    contract_id: Mapped[str] = mapped_column(String(25), nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    effective_from: Mapped[date] = mapped_column(Date, nullable=False)
    effective_until: Mapped[date | None] = mapped_column(Date, nullable=True)
    geographic_scope: Mapped[str | None] = mapped_column(String(255), nullable=True)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    caps: Mapped[list[dict]] = mapped_column(JSONB, nullable=False, server_default="[]")
    eligible_dependent_relations: Mapped[list[str]] = mapped_column(
        JSONB, nullable=False, server_default="[]"
    )
    is_active: Mapped[bool] = mapped_column(nullable=False, default=True, server_default="true")
    created_by: Mapped[str | None] = mapped_column(String(25), nullable=True)


class AuthorizationModel(CuidMixin, TenantMixin, Base, TimestampMixin):
    __tablename__ = "authorizations"

    case_id: Mapped[str] = mapped_column(
        ForeignKey("cases.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    clinical_subject_id: Mapped[str] = mapped_column(String(25), nullable=False, index=True)
    programme_id: Mapped[str] = mapped_column(
        ForeignKey("eap_programmes.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    service_category: Mapped[str] = mapped_column(
        String(50), ForeignKey("service_categories.code"), nullable=False, index=True
    )
    sessions_granted: Mapped[int] = mapped_column(Integer, nullable=False)
    sessions_used: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    status: Mapped[AuthorizationStatus] = mapped_column(
        EnumValueType(AuthorizationStatus),
        nullable=False,
        default=AuthorizationStatus.ACTIVE,
        index=True,
    )
    granted_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    expires_on: Mapped[date | None] = mapped_column(Date, nullable=True)
    extension_requested_sessions: Mapped[int | None] = mapped_column(Integer, nullable=True)
    extension_requested_by: Mapped[str | None] = mapped_column(String(25), nullable=True)
    extension_requested_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    extension_clinician_signoff: Mapped[str | None] = mapped_column(String(25), nullable=True)
    extension_admin_signoff: Mapped[str | None] = mapped_column(String(25), nullable=True)
    extended_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    closed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
