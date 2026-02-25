"""Refresh token storage for revocation and rotation."""

from datetime import UTC, datetime

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.infrastructure.models.refresh_token_model import RefreshTokenModel


class RefreshTokenRepository:
    """Persist and revoke refresh tokens by jti."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def save(self, jti: str, user_id: str, tenant_id: str) -> None:
        """Store a refresh token."""
        row = RefreshTokenModel(
            jti=jti,
            user_id=user_id,
            tenant_id=tenant_id,
        )
        self._session.add(row)

    async def is_valid(self, jti: str) -> bool:
        """Return True if the token exists and is not revoked."""
        result = await self._session.execute(
            select(RefreshTokenModel).where(
                RefreshTokenModel.jti == jti,
                RefreshTokenModel.revoked_at.is_(None),
            )
        )
        return result.scalar_one_or_none() is not None

    async def revoke(self, jti: str) -> None:
        """Mark the refresh token as revoked."""
        result = await self._session.execute(
            select(RefreshTokenModel).where(RefreshTokenModel.jti == jti)
        )
        row = result.scalar_one_or_none()
        if row:
            row.revoked_at = datetime.now(UTC)

    async def revoke_all_for_user(self, user_id: str) -> None:
        """Revoke all refresh tokens for the given user (e.g. on login)."""
        await self._session.execute(
            update(RefreshTokenModel)
            .where(
                RefreshTokenModel.user_id == user_id,
                RefreshTokenModel.revoked_at.is_(None),
            )
            .values(revoked_at=datetime.now(UTC))
        )
