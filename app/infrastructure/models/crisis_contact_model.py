"""Crisis contact model."""

from datetime import datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.domain.enums import (
    CrisisCallerRelation,
    CrisisContactOutcome,
    CrisisWarmHandoff,
    TriageRiskLevel,
)
from app.infrastructure.models.base import (
    Base,
    CuidMixin,
    EnumValueType,
    TenantMixin,
    TimestampMixin,
)


class CrisisContactModel(CuidMixin, TenantMixin, Base, TimestampMixin):
    __tablename__ = "crisis_contacts"

    contacted_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, index=True
    )
    caller_relation: Mapped[CrisisCallerRelation] = mapped_column(
        EnumValueType(CrisisCallerRelation), nullable=False, index=True
    )
    presenting_concern: Mapped[str] = mapped_column(Text, nullable=False)
    clinical_subject_id: Mapped[str | None] = mapped_column(
        String(25), nullable=True, index=True
    )
    case_id: Mapped[str | None] = mapped_column(
        ForeignKey("cases.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    counsellor_id: Mapped[str | None] = mapped_column(
        String(25), nullable=True, index=True
    )
    cssrs_administered: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=False
    )
    risk_assessment_id: Mapped[str | None] = mapped_column(
        String(25), nullable=True
    )
    safety_plan_id: Mapped[str | None] = mapped_column(
        String(25), nullable=True
    )
    risk_level: Mapped[TriageRiskLevel | None] = mapped_column(
        EnumValueType(TriageRiskLevel), nullable=True, index=True
    )
    warm_handoff: Mapped[CrisisWarmHandoff] = mapped_column(
        EnumValueType(CrisisWarmHandoff),
        nullable=False,
        default=CrisisWarmHandoff.NONE,
        index=True,
    )
    dispatched_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    outcome: Mapped[CrisisContactOutcome | None] = mapped_column(
        EnumValueType(CrisisContactOutcome), nullable=True, index=True
    )
    resolved_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    transcript_summary: Mapped[str | None] = mapped_column(Text, nullable=True)
