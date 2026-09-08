"""Survey campaign + response models (Phase 3 #D-Survey)."""

from datetime import date, datetime
from typing import Any

from sqlalchemy import (
    Boolean,
    Date,
    DateTime,
    ForeignKey,
    Integer,
    String,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.domain.enums import SurveyCampaignStatus
from app.infrastructure.models.base import (
    Base,
    CuidMixin,
    EnumValueType,
    TenantMixin,
    TimestampMixin,
)


class SurveyCampaignModel(CuidMixin, TenantMixin, Base, TimestampMixin):
    __tablename__ = "survey_campaigns"

    client_id: Mapped[str] = mapped_column(String(25), nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    source: Mapped[str] = mapped_column(
        String(50),
        ForeignKey("survey_sources.code"),
        nullable=False,
        index=True,
    )
    external_form_id: Mapped[str] = mapped_column(String(255), nullable=False)
    webhook_secret: Mapped[str] = mapped_column(String(255), nullable=False)
    status: Mapped[SurveyCampaignStatus] = mapped_column(
        EnumValueType(SurveyCampaignStatus),
        nullable=False,
        default=SurveyCampaignStatus.DRAFT,
        index=True,
    )
    period_start: Mapped[date | None] = mapped_column(Date, nullable=True)
    period_end: Mapped[date | None] = mapped_column(Date, nullable=True)
    anonymous: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    approved_questions: Mapped[list[dict[str, Any]]] = mapped_column(
        JSONB, nullable=False, server_default="[]"
    )
    response_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    created_by: Mapped[str] = mapped_column(String(25), nullable=False)
    activated_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    closed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)


class SurveyResponseModel(CuidMixin, TenantMixin, Base, TimestampMixin):
    __tablename__ = "survey_responses"
    __table_args__ = (
        UniqueConstraint(
            "campaign_id",
            "external_response_id",
            name="uq_survey_response_external_id_per_campaign",
        ),
    )

    campaign_id: Mapped[str] = mapped_column(
        ForeignKey("survey_campaigns.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    external_response_id: Mapped[str] = mapped_column(String(255), nullable=False)
    submitted_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, index=True
    )
    received_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    payload: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False)
    metrics: Mapped[dict[str, Any] | None] = mapped_column(JSONB, nullable=True)
