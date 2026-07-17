"""Outcome-measure + fitness-for-duty + return-to-work-plan models."""

from datetime import date, datetime

from sqlalchemy import (
    Boolean,
    Date,
    DateTime,
    Float,
    ForeignKey,
    String,
    Text,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.domain.enums import (
    FitnessForDutyOutcome,
    ReturnToWorkPlanStatus,
    TriageInstrumentCode,
)
from app.infrastructure.models.base import (
    Base,
    CuidMixin,
    EnumValueType,
    TenantMixin,
    TimestampMixin,
)


class OutcomeMeasureModel(CuidMixin, TenantMixin, Base, TimestampMixin):
    __tablename__ = "outcome_measures"

    case_id: Mapped[str] = mapped_column(
        ForeignKey("cases.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    clinical_subject_id: Mapped[str] = mapped_column(String(25), nullable=False, index=True)
    instrument_code: Mapped[TriageInstrumentCode] = mapped_column(
        EnumValueType(TriageInstrumentCode), nullable=False, index=True
    )
    intake_response_id: Mapped[str] = mapped_column(String(25), nullable=False)
    closure_response_id: Mapped[str] = mapped_column(String(25), nullable=False)
    pre_score: Mapped[float] = mapped_column(Float, nullable=False)
    post_score: Mapped[float] = mapped_column(Float, nullable=False)
    delta: Mapped[float] = mapped_column(Float, nullable=False)
    reliable_change_index: Mapped[float] = mapped_column(Float, nullable=False)
    meets_clinically_significant_change: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=False
    )
    recorded_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)


class FitnessForDutyModel(CuidMixin, TenantMixin, Base, TimestampMixin):
    __tablename__ = "fitness_for_duty"

    clinical_subject_id: Mapped[str] = mapped_column(String(25), nullable=False, index=True)
    client_id: Mapped[str] = mapped_column(String(25), nullable=False, index=True)
    requested_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, index=True
    )
    requested_by: Mapped[str] = mapped_column(String(25), nullable=False)
    business_necessity_rationale: Mapped[str] = mapped_column(Text, nullable=False)
    job_role_summary: Mapped[str] = mapped_column(Text, nullable=False)
    outcome: Mapped[FitnessForDutyOutcome] = mapped_column(
        EnumValueType(FitnessForDutyOutcome),
        nullable=False,
        default=FitnessForDutyOutcome.PENDING,
        index=True,
    )
    case_id: Mapped[str | None] = mapped_column(String(25), nullable=True, index=True)
    assessed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    assessor_id: Mapped[str | None] = mapped_column(String(25), nullable=True)
    accommodation_recommendations: Mapped[list[str]] = mapped_column(
        JSONB, nullable=False, server_default="[]"
    )
    employer_report_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )


class ReturnToWorkPlanModel(CuidMixin, TenantMixin, Base, TimestampMixin):
    __tablename__ = "return_to_work_plans"

    clinical_subject_id: Mapped[str] = mapped_column(String(25), nullable=False, index=True)
    client_id: Mapped[str] = mapped_column(String(25), nullable=False, index=True)
    starts_on: Mapped[date] = mapped_column(Date, nullable=False)
    ends_on: Mapped[date | None] = mapped_column(Date, nullable=True)
    status: Mapped[ReturnToWorkPlanStatus] = mapped_column(
        EnumValueType(ReturnToWorkPlanStatus),
        nullable=False,
        default=ReturnToWorkPlanStatus.DRAFT,
        index=True,
    )
    accommodations: Mapped[list[dict]] = mapped_column(JSONB, nullable=False, server_default="[]")
    case_id: Mapped[str | None] = mapped_column(String(25), nullable=True, index=True)
    fitness_for_duty_id: Mapped[str | None] = mapped_column(String(25), nullable=True, index=True)
    employer_signoff_user_id: Mapped[str | None] = mapped_column(String(25), nullable=True)
    clinician_signoff_user_id: Mapped[str | None] = mapped_column(String(25), nullable=True)
    activated_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    cancelled_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    cancellation_reason: Mapped[str | None] = mapped_column(Text, nullable=True)
    review_at: Mapped[date | None] = mapped_column(Date, nullable=True)
