"""Independent provider/practitioner persistence."""

from sqlalchemy import JSON, Enum, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column

from app.domain.enums import BaseStatus
from app.infrastructure.models.base import (
    Base,
    CuidMixin,
    SoftDeleteMixin,
    TenantMixin,
    TimestampMixin,
)


class ProviderModel(CuidMixin, TenantMixin, Base, TimestampMixin, SoftDeleteMixin):
    __tablename__ = "providers"

    user_id: Mapped[str] = mapped_column(
        String(25), ForeignKey("users.id", ondelete="RESTRICT"), nullable=False, index=True
    )
    status: Mapped[BaseStatus] = mapped_column(
        Enum(BaseStatus, name="basestatus", create_type=False, values_callable=lambda x: [e.value for e in x]),
        nullable=False,
        default=BaseStatus.PENDING,
    )
    license_info: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    provider_profile: Mapped[dict | None] = mapped_column(JSON, nullable=True)
