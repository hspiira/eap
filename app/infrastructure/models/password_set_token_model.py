"""
Password set token SQLAlchemy model.

One-time token for setting initial admin password after tenant registration.
Stored by token_hash; used_at marks redemption.
"""

from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column

from app.infrastructure.models.base import Base, CuidMixin


class PasswordSetTokenModel(CuidMixin, Base):
    """
    One-time token for POST /auth/set-initial-password.

    Created when a tenant is registered; user visits set_password_url,
    submits token + new password, then can log in.
    """

    __tablename__ = "password_set_tokens"

    token_hash: Mapped[str] = mapped_column(
        String(64), unique=True, nullable=False, index=True
    )
    user_id: Mapped[str] = mapped_column(
        String(25),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    expires_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False
    )
    used_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
