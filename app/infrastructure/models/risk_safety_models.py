"""Risk-safety models: assessments, plans, mandatory reports, caring contacts."""

from datetime import datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.domain.enums import (
    CaringContactChannel,
    CaringContactOutcome,
    MandatoryReportType,
    SafetyPlanStatus,
    TriageRiskLevel,
)
from app.infrastructure.models.base import (
    Base,
    CuidMixin,
    EnumValueType,
    TenantMixin,
    TimestampMixin,
)


class RiskAssessmentModel(CuidMixin, TenantMixin, Base, TimestampMixin):
    __tablename__ = "risk_assessments"

    clinical_subject_id: Mapped[str] = mapped_column(String(25), nullable=False, index=True)
    case_id: Mapped[str | None] = mapped_column(
        ForeignKey("cases.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    crisis_contact_id: Mapped[str | None] = mapped_column(
        ForeignKey("crisis_contacts.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    assessor_id: Mapped[str] = mapped_column(String(25), nullable=False)
    assessed_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, index=True
    )
    risk_level: Mapped[TriageRiskLevel] = mapped_column(
        EnumValueType(TriageRiskLevel), nullable=False, index=True
    )
    imminent_harm_to_self: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    imminent_harm_to_others: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    child_safety_concern: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    vulnerable_adult_concern: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    requires_safety_plan: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    requires_mandatory_report: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=False, index=True
    )
    rationale: Mapped[str] = mapped_column(Text, nullable=False)
    questionnaire_response_ids: Mapped[list[str]] = mapped_column(
        JSONB, nullable=False, server_default="[]"
    )


class SafetyPlanModel(CuidMixin, TenantMixin, Base, TimestampMixin):
    __tablename__ = "safety_plans"

    clinical_subject_id: Mapped[str] = mapped_column(String(25), nullable=False, index=True)
    case_id: Mapped[str | None] = mapped_column(String(25), nullable=True, index=True)
    crisis_contact_id: Mapped[str | None] = mapped_column(String(25), nullable=True, index=True)
    clinician_id: Mapped[str] = mapped_column(String(25), nullable=False)
    status: Mapped[SafetyPlanStatus] = mapped_column(
        EnumValueType(SafetyPlanStatus),
        nullable=False,
        default=SafetyPlanStatus.DRAFT,
        index=True,
    )
    warning_signs: Mapped[list[str]] = mapped_column(JSONB, nullable=False, server_default="[]")
    internal_coping_strategies: Mapped[list[str]] = mapped_column(
        JSONB, nullable=False, server_default="[]"
    )
    social_distractions: Mapped[list[str]] = mapped_column(
        JSONB, nullable=False, server_default="[]"
    )
    social_contacts_for_help: Mapped[list[dict]] = mapped_column(
        JSONB, nullable=False, server_default="[]"
    )
    professional_help_resources: Mapped[list[dict]] = mapped_column(
        JSONB, nullable=False, server_default="[]"
    )
    means_restriction_plan: Mapped[list[str]] = mapped_column(
        JSONB, nullable=False, server_default="[]"
    )
    activated_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    next_review_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    reviewed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    reviewed_by: Mapped[str | None] = mapped_column(String(25), nullable=True)
    supersedes_safety_plan_id: Mapped[str | None] = mapped_column(String(25), nullable=True)
    superseded_by: Mapped[str | None] = mapped_column(String(25), nullable=True)
    superseded_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)


class MandatoryReportModel(CuidMixin, TenantMixin, Base, TimestampMixin):
    __tablename__ = "mandatory_reports"

    clinical_subject_id: Mapped[str] = mapped_column(String(25), nullable=False, index=True)
    risk_assessment_id: Mapped[str] = mapped_column(
        ForeignKey("risk_assessments.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    case_id: Mapped[str | None] = mapped_column(String(25), nullable=True, index=True)
    crisis_contact_id: Mapped[str | None] = mapped_column(String(25), nullable=True, index=True)
    report_type: Mapped[MandatoryReportType] = mapped_column(
        EnumValueType(MandatoryReportType), nullable=False, index=True
    )
    submitted_to: Mapped[str] = mapped_column(String(255), nullable=False)
    submitted_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, index=True
    )
    submitted_by: Mapped[str] = mapped_column(String(25), nullable=False)
    external_reference_number: Mapped[str | None] = mapped_column(String(255), nullable=True)
    contact_email: Mapped[str | None] = mapped_column(String(255), nullable=True)
    contact_phone: Mapped[str | None] = mapped_column(String(50), nullable=True)


class CaringContactModel(CuidMixin, TenantMixin, Base, TimestampMixin):
    __tablename__ = "caring_contacts"

    clinical_subject_id: Mapped[str] = mapped_column(String(25), nullable=False, index=True)
    crisis_contact_id: Mapped[str] = mapped_column(
        ForeignKey("crisis_contacts.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    case_id: Mapped[str | None] = mapped_column(String(25), nullable=True, index=True)
    channel: Mapped[CaringContactChannel] = mapped_column(
        EnumValueType(CaringContactChannel), nullable=False
    )
    due_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, index=True)
    outcome: Mapped[CaringContactOutcome] = mapped_column(
        EnumValueType(CaringContactOutcome),
        nullable=False,
        default=CaringContactOutcome.PENDING,
        index=True,
    )
    attempted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    handled_by: Mapped[str | None] = mapped_column(String(25), nullable=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
