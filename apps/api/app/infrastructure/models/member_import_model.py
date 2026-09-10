"""Staged member roster import persistence."""

from datetime import datetime

from sqlalchemy import (
    DateTime,
    ForeignKey,
    ForeignKeyConstraint,
    Integer,
    String,
    Text,
    UniqueConstraint,
    text,
)
from sqlalchemy import (
    Index as SAIndex,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.domain.enums.person import MemberImportRowOutcome
from app.domain.enums.provider_network import ImportBatchStatus
from app.infrastructure.models.base import (
    Base,
    CuidMixin,
    EnumValueType,
    TenantMixin,
    TimestampMixin,
)


class MemberImportBatchModel(CuidMixin, TenantMixin, Base, TimestampMixin):
    """One roster upload and its provenance.

    Only a batch still awaiting a decision holds its file hash: an applied or
    abandoned batch does not block restaging the same roster.
    """

    __tablename__ = "member_import_batches"
    __table_args__ = (
        UniqueConstraint("tenant_id", "id", name="uq_member_import_batches_tenant"),
        SAIndex(
            "uq_member_import_batches_tenant_file_hash",
            "tenant_id",
            "file_hash",
            unique=True,
            postgresql_where=text("status = 'Staged'"),
        ),
    )

    file_name: Mapped[str] = mapped_column(String(500), nullable=False)
    file_hash: Mapped[str] = mapped_column(String(128), nullable=False, index=True)
    row_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    status: Mapped[ImportBatchStatus] = mapped_column(
        EnumValueType(ImportBatchStatus),
        nullable=False,
        default=ImportBatchStatus.STAGED,
        index=True,
    )
    staged_by: Mapped[str] = mapped_column(String(25), nullable=False)
    applied_by: Mapped[str | None] = mapped_column(String(25), nullable=True)
    applied_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)


class MemberImportRowModel(CuidMixin, TenantMixin, Base, TimestampMixin):
    """One roster row, its outcome, and the decision made about it."""

    __tablename__ = "member_import_rows"
    __table_args__ = (
        UniqueConstraint("batch_id", "row_number", name="uq_member_import_rows_batch_row"),
        UniqueConstraint("tenant_id", "replay_key", name="uq_member_import_rows_tenant_replay"),
        ForeignKeyConstraint(
            ["tenant_id", "batch_id"],
            ["member_import_batches.tenant_id", "member_import_batches.id"],
            name="fk_member_import_rows_tenant_batch",
            ondelete="CASCADE",
        ),
    )

    batch_id: Mapped[str] = mapped_column(String(25), nullable=False, index=True)
    row_number: Mapped[int] = mapped_column(Integer, nullable=False)
    replay_key: Mapped[str] = mapped_column(String(500), nullable=False, index=True)
    client_code: Mapped[str | None] = mapped_column(String(100), nullable=True)
    client_id: Mapped[str | None] = mapped_column(String(25), nullable=True, index=True)
    import_source_id: Mapped[str | None] = mapped_column(String(255), nullable=True)
    staff_number: Mapped[str | None] = mapped_column(String(100), nullable=True)
    display_label: Mapped[str | None] = mapped_column(String(255), nullable=True)
    work_email: Mapped[str | None] = mapped_column(String(255), nullable=True)
    personal_email: Mapped[str | None] = mapped_column(String(255), nullable=True)
    gender: Mapped[str | None] = mapped_column(String(50), nullable=True)
    date_of_birth: Mapped[str | None] = mapped_column(String(20), nullable=True)
    date_joined: Mapped[str | None] = mapped_column(String(20), nullable=True)
    phone: Mapped[str | None] = mapped_column(String(50), nullable=True)
    national_id: Mapped[str | None] = mapped_column(String(100), nullable=True)
    passport_number: Mapped[str | None] = mapped_column(String(100), nullable=True)
    job_title: Mapped[str | None] = mapped_column(String(255), nullable=True)
    job_classification: Mapped[str | None] = mapped_column(String(255), nullable=True)
    skill: Mapped[str | None] = mapped_column(String(255), nullable=True)
    department: Mapped[str | None] = mapped_column(String(255), nullable=True)
    unit: Mapped[str | None] = mapped_column(String(255), nullable=True)
    employment_type: Mapped[str | None] = mapped_column(String(255), nullable=True)
    status: Mapped[str | None] = mapped_column(String(50), nullable=True)
    relation: Mapped[str | None] = mapped_column(String(50), nullable=True)
    primary_import_source_id: Mapped[str | None] = mapped_column(String(255), nullable=True)
    outcome: Mapped[MemberImportRowOutcome] = mapped_column(
        EnumValueType(MemberImportRowOutcome), nullable=False, index=True
    )
    decision: Mapped[str] = mapped_column(String(10), nullable=False)
    message: Mapped[str | None] = mapped_column(Text, nullable=True)
    imported_member_id: Mapped[str | None] = mapped_column(
        String(25), ForeignKey("eligible_members.id", ondelete="SET NULL"), nullable=True
    )
