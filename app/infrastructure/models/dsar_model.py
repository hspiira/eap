"""DSAR request model (Phase 4 #DSAR)."""

from datetime import datetime
from typing import Any

from sqlalchemy import DateTime, String, Text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.domain.enums import DSARRequestStatus, DSARRequestType
from app.infrastructure.models.base import (
    Base,
    CuidMixin,
    EnumValueType,
    TenantMixin,
    TimestampMixin,
)


class DSARRequestModel(CuidMixin, TenantMixin, Base, TimestampMixin):
    __tablename__ = "dsar_requests"

    subject_person_id: Mapped[str] = mapped_column(
        String(25), nullable=False, index=True
    )
    request_type: Mapped[DSARRequestType] = mapped_column(
        EnumValueType(DSARRequestType), nullable=False, index=True
    )
    status: Mapped[DSARRequestStatus] = mapped_column(
        EnumValueType(DSARRequestStatus),
        nullable=False,
        default=DSARRequestStatus.REQUESTED,
        index=True,
    )
    requested_by: Mapped[str] = mapped_column(String(25), nullable=False)
    started_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    completed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    failed_reason: Mapped[str | None] = mapped_column(Text, nullable=True)
    output: Mapped[dict[str, Any] | None] = mapped_column(JSONB, nullable=True)
    erasure_executes_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True, index=True
    )
