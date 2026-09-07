"""Staged historical session import persistence."""

from datetime import date, datetime

from sqlalchemy import (
    JSON,
    Date,
    DateTime,
    ForeignKey,
    ForeignKeyConstraint,
    Index,
    Integer,
    String,
    Text,
    UniqueConstraint,
    text,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.domain.enums.provider_network import (
    DeliveryContext,
    ImportBatchStatus,
    ImportRowOutcome,
)
from app.infrastructure.models.base import (
    Base,
    CuidMixin,
    EnumValueType,
    TenantMixin,
    TimestampMixin,
)


class SessionImportBatchModel(CuidMixin, TenantMixin, Base, TimestampMixin):
    """One import attempt and its provenance.

    The tenant/hash uniqueness makes restaging the same file within a tenant an
    explicit conflict rather than a silent second batch. It skips abandoned
    batches: one was superseded on purpose, and holding its hash would mean an
    extract could never be staged again once the review data it waited on had
    arrived.
    """

    __tablename__ = "session_import_batches"
    __table_args__ = (
        UniqueConstraint("tenant_id", "id", name="uq_session_import_batches_tenant"),
        Index(
            "uq_session_import_batches_tenant_file_hash",
            "tenant_id",
            "file_hash",
            unique=True,
            postgresql_where=text("status <> 'Abandoned'"),
        ),
    )

    source_system: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    file_name: Mapped[str] = mapped_column(String(500), nullable=False)
    file_hash: Mapped[str] = mapped_column(String(128), nullable=False, index=True)
    row_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    source_record_key_field: Mapped[str | None] = mapped_column(String(100), nullable=True)
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


class SessionImportRowModel(CuidMixin, TenantMixin, Base, TimestampMixin):
    """One source row and its reconciliation outcome.

    `replay_key` is unique per tenant, so replaying the same file cannot create
    a second staged row for the same source record.
    """

    __tablename__ = "session_import_rows"
    __table_args__ = (
        UniqueConstraint("batch_id", "row_number", name="uq_session_import_rows_batch_row_number"),
        UniqueConstraint("tenant_id", "replay_key", name="uq_session_import_rows_tenant_replay"),
        ForeignKeyConstraint(
            ["tenant_id", "batch_id"],
            ["session_import_batches.tenant_id", "session_import_batches.id"],
            name="fk_session_import_rows_tenant_batch",
            ondelete="CASCADE",
        ),
        ForeignKeyConstraint(
            ["tenant_id", "provider_id"],
            ["providers.tenant_id", "providers.id"],
            name="fk_session_import_rows_tenant_provider",
            ondelete="RESTRICT",
        ),
        ForeignKeyConstraint(
            ["tenant_id", "provider_affiliation_id", "provider_id"],
            [
                "provider_affiliations.tenant_id",
                "provider_affiliations.id",
                "provider_affiliations.provider_id",
            ],
            name="fk_session_import_rows_tenant_affiliation_provider",
            ondelete="RESTRICT",
        ),
    )

    batch_id: Mapped[str] = mapped_column(String(25), nullable=False, index=True)
    row_number: Mapped[int] = mapped_column(Integer, nullable=False)
    replay_key: Mapped[str] = mapped_column(String(500), nullable=False, index=True)
    source_record_key: Mapped[str | None] = mapped_column(String(255), nullable=True)
    raw_practitioner_name: Mapped[str | None] = mapped_column(String(500), nullable=True)
    session_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    outcome: Mapped[ImportRowOutcome] = mapped_column(
        EnumValueType(ImportRowOutcome), nullable=False, index=True
    )
    delivery_context: Mapped[DeliveryContext] = mapped_column(
        EnumValueType(DeliveryContext),
        nullable=False,
        default=DeliveryContext.UNKNOWN,
        index=True,
    )
    provider_id: Mapped[str | None] = mapped_column(String(25), nullable=True, index=True)
    provider_affiliation_id: Mapped[str | None] = mapped_column(String(25), nullable=True)
    reasons: Mapped[list | None] = mapped_column(JSON, nullable=True)
    client_id: Mapped[str | None] = mapped_column(String(25), nullable=True, index=True)
    attendance: Mapped[str | None] = mapped_column(String(32), nullable=True)
    member_id: Mapped[str | None] = mapped_column(String(25), nullable=True, index=True)
    service_id: Mapped[str | None] = mapped_column(String(25), nullable=True)
    session_type: Mapped[str | None] = mapped_column(String(32), nullable=True)
    category: Mapped[str | None] = mapped_column(String(32), nullable=True)
    clinical_outcome: Mapped[str | None] = mapped_column(String(32), nullable=True)
    session_status: Mapped[str | None] = mapped_column(String(32), nullable=True)
    client_type: Mapped[str | None] = mapped_column(String(32), nullable=True)
    rate_ugx: Mapped[int | None] = mapped_column(Integer, nullable=True)
    session_number: Mapped[int | None] = mapped_column(Integer, nullable=True)
    imported_session_id: Mapped[str | None] = mapped_column(
        String(25), ForeignKey("service_sessions.id", ondelete="SET NULL"), nullable=True
    )
