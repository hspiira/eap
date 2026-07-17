"""Manager-workspace models."""

from datetime import date, datetime

from sqlalchemy import Boolean, Date, DateTime, String, Text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.domain.enums import (
    ManagerConsultTopic,
    TrainingEnrolmentStatus,
    WorkLifeReferralOutcome,
    WorkLifeServiceType,
)
from app.infrastructure.models.base import (
    Base,
    CuidMixin,
    EnumValueType,
    TenantMixin,
    TimestampMixin,
)


class ManagerConsultModel(CuidMixin, TenantMixin, Base, TimestampMixin):
    __tablename__ = "manager_consults"

    manager_id: Mapped[str] = mapped_column(String(25), nullable=False, index=True)
    consultant_id: Mapped[str] = mapped_column(String(25), nullable=False)
    topic: Mapped[ManagerConsultTopic] = mapped_column(
        EnumValueType(ManagerConsultTopic), nullable=False, index=True
    )
    consulted_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, index=True
    )
    notes: Mapped[str] = mapped_column(Text, nullable=False)
    client_id: Mapped[str | None] = mapped_column(String(25), nullable=True, index=True)
    triggered_referral_case_id: Mapped[str | None] = mapped_column(
        String(25), nullable=True, index=True
    )
    closed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)


class WorkLifeProviderModel(CuidMixin, TenantMixin, Base, TimestampMixin):
    __tablename__ = "work_life_providers"

    name: Mapped[str] = mapped_column(String(255), nullable=False)
    service_types: Mapped[list[str]] = mapped_column(JSONB, nullable=False, server_default="[]")
    is_active: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=True, server_default="true"
    )
    contact_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    contact_email: Mapped[str | None] = mapped_column(String(255), nullable=True)
    contact_phone: Mapped[str | None] = mapped_column(String(50), nullable=True)
    coverage_notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    rate_card_notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    last_verified_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    deactivated_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)


class WorkLifeReferralModel(CuidMixin, TenantMixin, Base, TimestampMixin):
    __tablename__ = "work_life_referrals"

    clinical_subject_id: Mapped[str] = mapped_column(String(25), nullable=False, index=True)
    service_type: Mapped[WorkLifeServiceType] = mapped_column(
        EnumValueType(WorkLifeServiceType), nullable=False, index=True
    )
    requested_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, index=True
    )
    outcome: Mapped[WorkLifeReferralOutcome] = mapped_column(
        EnumValueType(WorkLifeReferralOutcome),
        nullable=False,
        default=WorkLifeReferralOutcome.REQUESTED,
        index=True,
    )
    referred_provider_id: Mapped[str | None] = mapped_column(String(25), nullable=True, index=True)
    case_id: Mapped[str | None] = mapped_column(String(25), nullable=True, index=True)
    requested_by: Mapped[str | None] = mapped_column(String(25), nullable=True)
    resolution_notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    resolved_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)


class TrainingEnrolmentModel(CuidMixin, TenantMixin, Base, TimestampMixin):
    __tablename__ = "training_enrolments"

    trainee_id: Mapped[str] = mapped_column(String(25), nullable=False, index=True)
    document_id: Mapped[str] = mapped_column(String(25), nullable=False, index=True)
    status: Mapped[TrainingEnrolmentStatus] = mapped_column(
        EnumValueType(TrainingEnrolmentStatus),
        nullable=False,
        default=TrainingEnrolmentStatus.ENROLLED,
        index=True,
    )
    enrolled_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    expires_on: Mapped[date | None] = mapped_column(Date, nullable=True, index=True)
    revoked_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    revoked_reason: Mapped[str | None] = mapped_column(Text, nullable=True)
