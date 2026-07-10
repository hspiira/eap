"""Clinical case model."""

from datetime import datetime

from sqlalchemy import DateTime, String, Text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.domain.enums import (
    CaseClosureReason,
    CaseReferralSource,
    CaseStatus,
    PresentingProblem,
)
from app.infrastructure.models.base import (
    Base,
    CuidMixin,
    EnumValueType,
    TenantMixin,
    TimestampMixin,
)


class CaseModel(CuidMixin, TenantMixin, Base, TimestampMixin):
    __tablename__ = "cases"

    clinical_subject_id: Mapped[str] = mapped_column(
        String(25), nullable=False, index=True
    )
    client_id: Mapped[str] = mapped_column(
        String(25), nullable=False, index=True
    )
    presenting_problem: Mapped[PresentingProblem] = mapped_column(
        EnumValueType(PresentingProblem), nullable=False, index=True
    )
    referral_source: Mapped[CaseReferralSource] = mapped_column(
        EnumValueType(CaseReferralSource), nullable=False, index=True
    )
    status: Mapped[CaseStatus] = mapped_column(
        EnumValueType(CaseStatus),
        nullable=False,
        default=CaseStatus.INTAKE,
        index=True,
    )
    opened_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, index=True
    )
    assigned_counsellor_id: Mapped[str | None] = mapped_column(
        String(25), nullable=True, index=True
    )
    authorization_id: Mapped[str | None] = mapped_column(
        String(25), nullable=True, index=True
    )
    referred_by_user_id: Mapped[str | None] = mapped_column(
        String(25), nullable=True
    )
    referral_notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    closed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    closure_reason: Mapped[CaseClosureReason | None] = mapped_column(
        EnumValueType(CaseClosureReason), nullable=True
    )
    closure_summary_note_id: Mapped[str | None] = mapped_column(
        String(25), nullable=True
    )
    intake_screener_admin_ids: Mapped[list[str]] = mapped_column(
        JSONB, nullable=False, server_default="[]"
    )
    closure_screener_admin_ids: Mapped[list[str]] = mapped_column(
        JSONB, nullable=False, server_default="[]"
    )
