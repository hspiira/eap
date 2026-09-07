"""Staged practitioner workbook import persistence."""

from datetime import datetime

from sqlalchemy import (
    JSON,
    DateTime,
    ForeignKeyConstraint,
    Integer,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.domain.enums.provider_network import ImportBatchStatus, PractitionerImportOutcome
from app.infrastructure.models.base import (
    Base,
    CuidMixin,
    EnumValueType,
    TenantMixin,
    TimestampMixin,
)


class PractitionerImportBatchModel(CuidMixin, TenantMixin, Base, TimestampMixin):
    """One workbook staging attempt and its provenance.

    The tenant/hash uniqueness makes restaging the same file within a tenant
    an explicit conflict rather than a silent second batch.
    """

    __tablename__ = "practitioner_import_batches"
    __table_args__ = (
        UniqueConstraint("tenant_id", "id", name="uq_practitioner_import_batches_tenant"),
        UniqueConstraint(
            "tenant_id", "file_hash", name="uq_practitioner_import_batches_tenant_file_hash"
        ),
    )

    source_system: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
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


class PractitionerImportRowModel(CuidMixin, TenantMixin, Base, TimestampMixin):
    """One workbook row and its staging outcome.

    `replay_key` is unique per tenant and carries the sheet name, because the
    two practitioner sheets share row numbers.
    """

    __tablename__ = "practitioner_import_rows"
    __table_args__ = (
        UniqueConstraint(
            "batch_id",
            "sheet_name",
            "row_number",
            name="uq_practitioner_import_rows_batch_sheet_row",
        ),
        UniqueConstraint(
            "tenant_id", "replay_key", name="uq_practitioner_import_rows_tenant_replay"
        ),
        ForeignKeyConstraint(
            ["tenant_id", "batch_id"],
            ["practitioner_import_batches.tenant_id", "practitioner_import_batches.id"],
            name="fk_practitioner_import_rows_tenant_batch",
            ondelete="CASCADE",
        ),
    )

    batch_id: Mapped[str] = mapped_column(String(25), nullable=False, index=True)
    sheet_name: Mapped[str] = mapped_column(String(100), nullable=False)
    row_number: Mapped[int] = mapped_column(Integer, nullable=False)
    replay_key: Mapped[str] = mapped_column(String(500), nullable=False, index=True)
    raw_name: Mapped[str | None] = mapped_column(String(500), nullable=True)
    normalized_name: Mapped[str | None] = mapped_column(String(500), nullable=True, index=True)
    organisation_name: Mapped[str | None] = mapped_column(String(500), nullable=True)
    raw_profession: Mapped[str | None] = mapped_column(String(500), nullable=True)
    mapped_profession: Mapped[str | None] = mapped_column(String(255), nullable=True)
    contact_email: Mapped[str | None] = mapped_column(String(500), nullable=True)
    outcome: Mapped[PractitionerImportOutcome] = mapped_column(
        EnumValueType(PractitionerImportOutcome), nullable=False, index=True
    )
    reasons: Mapped[list | None] = mapped_column(JSON, nullable=True)
    provenance: Mapped[dict | None] = mapped_column(JSON, nullable=True)
