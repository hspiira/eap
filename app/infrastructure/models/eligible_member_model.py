"""Eligible-member + clinical-subject + audited link models (Phase 5A #5A.1)."""

from datetime import date, datetime

from sqlalchemy import (
    Boolean,
    Date,
    DateTime,
    ForeignKey,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.domain.enums import EligibilityStatus, MemberRelation
from app.infrastructure.models.base import (
    Base,
    CuidMixin,
    EnumValueType,
    TenantMixin,
    TimestampMixin,
)


class EligibleMemberModel(CuidMixin, TenantMixin, Base, TimestampMixin):
    __tablename__ = "eligible_members"
    __table_args__ = (
        UniqueConstraint(
            "tenant_id",
            "client_id",
            "employer_member_id",
            name="uq_eligible_member_employer_id_per_client",
        ),
    )

    client_id: Mapped[str] = mapped_column(String(25), nullable=False, index=True)
    employer_member_id: Mapped[str] = mapped_column(String(255), nullable=False)
    relation: Mapped[MemberRelation] = mapped_column(
        EnumValueType(MemberRelation), nullable=False, index=True
    )
    status: Mapped[EligibilityStatus] = mapped_column(
        EnumValueType(EligibilityStatus),
        nullable=False,
        default=EligibilityStatus.PENDING,
        index=True,
    )
    primary_employee_member_id: Mapped[str | None] = mapped_column(
        String(25), nullable=True, index=True
    )
    coverage_start: Mapped[date | None] = mapped_column(Date, nullable=True)
    coverage_end: Mapped[date | None] = mapped_column(Date, nullable=True)
    work_email: Mapped[str | None] = mapped_column(String(255), nullable=True)
    personal_email: Mapped[str | None] = mapped_column(String(255), nullable=True)
    display_label: Mapped[str | None] = mapped_column(String(255), nullable=True)
    last_imported_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    suspended_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    terminated_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    created_by: Mapped[str | None] = mapped_column(String(25), nullable=True)


class ClinicalSubjectModel(CuidMixin, TenantMixin, Base, TimestampMixin):
    __tablename__ = "clinical_subjects"
    __table_args__ = (
        UniqueConstraint(
            "tenant_id",
            "pseudonym",
            name="uq_clinical_subject_pseudonym_per_tenant",
        ),
    )

    pseudonym: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    preferred_language: Mapped[str | None] = mapped_column(
        String(20), nullable=True
    )
    preferred_pronouns: Mapped[str | None] = mapped_column(
        String(50), nullable=True
    )
    preferred_contact_method: Mapped[str | None] = mapped_column(
        String(20), nullable=True
    )
    notes_for_continuity: Mapped[str | None] = mapped_column(Text, nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    deactivated_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )


class EligibleMemberClinicalLinkModel(Base, TimestampMixin):
    __tablename__ = "eligible_member_clinical_link"
    __table_args__ = (
        UniqueConstraint(
            "tenant_id",
            "member_id",
            name="uq_link_member_per_tenant",
        ),
        UniqueConstraint(
            "tenant_id",
            "subject_id",
            name="uq_link_subject_per_tenant",
        ),
    )

    tenant_id: Mapped[str] = mapped_column(String(25), nullable=False, index=True)
    member_id: Mapped[str] = mapped_column(
        ForeignKey("eligible_members.id", ondelete="CASCADE"),
        nullable=False,
        primary_key=True,
    )
    subject_id: Mapped[str] = mapped_column(
        ForeignKey("clinical_subjects.id", ondelete="CASCADE"),
        nullable=False,
        primary_key=True,
    )
