"""Consent + DataSharingRegister + DPOContact models."""

from datetime import date, datetime

from sqlalchemy import Date, DateTime, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.domain.enums import (
    ConsentPurpose,
    ConsentScope,
    ConsentStatus,
)
from app.infrastructure.models.base import (
    Base,
    CuidMixin,
    EnumValueType,
    TenantMixin,
    TimestampMixin,
)


class ConsentModel(CuidMixin, TenantMixin, Base, TimestampMixin):
    __tablename__ = "consents"

    subject_clinical_subject_id: Mapped[str] = mapped_column(String(25), nullable=False, index=True)
    case_id: Mapped[str | None] = mapped_column(String(25), nullable=True, index=True)
    scope: Mapped[ConsentScope] = mapped_column(
        EnumValueType(ConsentScope), nullable=False, index=True
    )
    purpose: Mapped[ConsentPurpose] = mapped_column(
        EnumValueType(ConsentPurpose), nullable=False, index=True
    )
    purpose_other_detail: Mapped[str | None] = mapped_column(Text, nullable=True)
    disclosure_to: Mapped[str] = mapped_column(String(255), nullable=False)
    status: Mapped[ConsentStatus] = mapped_column(
        EnumValueType(ConsentStatus),
        nullable=False,
        default=ConsentStatus.PENDING,
        index=True,
    )
    requested_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    requested_by: Mapped[str] = mapped_column(String(25), nullable=False)
    expires_on: Mapped[date | None] = mapped_column(Date, nullable=True, index=True)
    granted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    granted_by_subject_reference: Mapped[str | None] = mapped_column(String(255), nullable=True)
    signed_artifact_document_id: Mapped[str | None] = mapped_column(String(25), nullable=True)
    revoked_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    revoked_reason: Mapped[str | None] = mapped_column(Text, nullable=True)


class DataSharingRegisterEntryModel(CuidMixin, TenantMixin, Base, TimestampMixin):
    __tablename__ = "data_sharing_register"

    subject_clinical_subject_id: Mapped[str] = mapped_column(String(25), nullable=False, index=True)
    consent_id: Mapped[str | None] = mapped_column(
        ForeignKey("consents.id", ondelete="RESTRICT"),
        nullable=True,
        index=True,
    )
    case_id: Mapped[str | None] = mapped_column(String(25), nullable=True, index=True)
    shared_with: Mapped[str] = mapped_column(String(255), nullable=False)
    scope: Mapped[ConsentScope] = mapped_column(EnumValueType(ConsentScope), nullable=False)
    summary_of_data_shared: Mapped[str] = mapped_column(Text, nullable=False)
    legal_basis: Mapped[str | None] = mapped_column(Text, nullable=True)
    shared_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, index=True)
    shared_by: Mapped[str] = mapped_column(String(25), nullable=False)
    delivery_channel: Mapped[str | None] = mapped_column(String(50), nullable=True)
    delivery_reference: Mapped[str | None] = mapped_column(String(255), nullable=True)


class DPOContactModel(CuidMixin, TenantMixin, Base, TimestampMixin):
    __tablename__ = "dpo_contacts"

    full_name: Mapped[str] = mapped_column(String(255), nullable=False)
    email: Mapped[str] = mapped_column(String(255), nullable=False)
    phone: Mapped[str | None] = mapped_column(String(50), nullable=True)
    role_title: Mapped[str | None] = mapped_column(String(255), nullable=True)
    effective_from: Mapped[date] = mapped_column(Date, nullable=False)
    effective_until: Mapped[date | None] = mapped_column(Date, nullable=True, index=True)
    appointed_by: Mapped[str | None] = mapped_column(String(25), nullable=True)
