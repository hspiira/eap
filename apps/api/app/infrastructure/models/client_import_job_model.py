"""SQLAlchemy model for durable client import jobs."""

from datetime import datetime

from sqlalchemy import JSON, LargeBinary, String
from sqlalchemy.orm import Mapped, mapped_column

from app.infrastructure.models.base import Base, CuidMixin, TenantMixin, TimestampMixin


class ClientImportJobModel(CuidMixin, TenantMixin, Base, TimestampMixin):
    """Persisted payload, progress, and result for an asynchronous import."""

    __tablename__ = "client_import_jobs"

    requested_by: Mapped[str] = mapped_column(String(25), nullable=False, index=True)
    filename: Mapped[str] = mapped_column(String(255), nullable=False)
    file_size: Mapped[int] = mapped_column(nullable=False)
    file_content: Mapped[bytes] = mapped_column(LargeBinary, nullable=False)
    decisions: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)
    status: Mapped[str] = mapped_column(String(20), nullable=False, index=True)
    total_rows: Mapped[int] = mapped_column(nullable=False, default=0)
    processed_rows: Mapped[int] = mapped_column(nullable=False, default=0)
    imported: Mapped[int] = mapped_column(nullable=False, default=0)
    skipped: Mapped[int] = mapped_column(nullable=False, default=0)
    failed: Mapped[int] = mapped_column(nullable=False, default=0)
    retry_count: Mapped[int] = mapped_column(nullable=False, default=0)
    issues: Mapped[list] = mapped_column(JSON, nullable=False, default=list)
    error_message: Mapped[str | None] = mapped_column(String(1000), nullable=True)
    started_at: Mapped[datetime | None] = mapped_column(nullable=True)
    completed_at: Mapped[datetime | None] = mapped_column(nullable=True)
