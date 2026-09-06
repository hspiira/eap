"""Care Callback campaign + outreach models (Phase 3 #D-CareCallback)."""

from datetime import date, datetime
from typing import Any

from sqlalchemy import (
    Boolean,
    Date,
    DateTime,
    ForeignKey,
    ForeignKeyConstraint,
    Integer,
    String,
    Text,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.domain.enums import (
    CareCallbackCampaignStatus,
    OutreachStatus,
    TriageRiskLevel,
)
from app.infrastructure.models.base import (
    Base,
    CuidMixin,
    EnumValueType,
    TenantMixin,
    TimestampMixin,
)


class CareCallbackCampaignModel(CuidMixin, TenantMixin, Base, TimestampMixin):
    __tablename__ = "care_callback_campaigns"

    client_id: Mapped[str] = mapped_column(String(25), nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    period_start: Mapped[date] = mapped_column(Date, nullable=False, index=True)
    period_end: Mapped[date] = mapped_column(Date, nullable=False, index=True)
    target_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    completed_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    counsellor_pool: Mapped[list[str]] = mapped_column(JSONB, nullable=False, server_default="[]")
    status: Mapped[CareCallbackCampaignStatus] = mapped_column(
        EnumValueType(CareCallbackCampaignStatus),
        nullable=False,
        default=CareCallbackCampaignStatus.DRAFT,
        index=True,
    )
    sampling_notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_by: Mapped[str] = mapped_column(String(25), nullable=False)
    activated_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    completed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True, index=True
    )


class OutreachRecordModel(CuidMixin, TenantMixin, Base, TimestampMixin):
    __tablename__ = "outreach_records"
    __table_args__ = (
        ForeignKeyConstraint(
            ["tenant_id", "counsellor_id"],
            ["providers.tenant_id", "providers.id"],
            name="fk_outreach_records_counsellor_tenant",
            ondelete="RESTRICT",
        ),
    )

    campaign_id: Mapped[str] = mapped_column(
        ForeignKey("care_callback_campaigns.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    member_id: Mapped[str] = mapped_column(
        ForeignKey("eligible_members.id", ondelete="RESTRICT"), nullable=False, index=True
    )
    counsellor_id: Mapped[str | None] = mapped_column(String(25), nullable=True, index=True)
    status: Mapped[OutreachStatus] = mapped_column(
        EnumValueType(OutreachStatus),
        nullable=False,
        default=OutreachStatus.PENDING,
        index=True,
    )
    contact_attempts: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    assigned_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    last_attempted_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    triage_instrument_code: Mapped[str | None] = mapped_column(String(100), nullable=True)
    triage_responses: Mapped[dict[str, Any] | None] = mapped_column(JSONB, nullable=True)
    triage_scores: Mapped[dict[str, Any] | None] = mapped_column(JSONB, nullable=True)
    triage_risk_level: Mapped[TriageRiskLevel | None] = mapped_column(
        EnumValueType(TriageRiskLevel), nullable=True, index=True
    )
    crisis_flag: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
