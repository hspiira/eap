"""
Database Configuration

Async SQLAlchemy setup for FastAPI application.
"""

from collections.abc import AsyncGenerator

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.core.config import settings
from app.infrastructure.models.base import Base

# pool_pre_ping detects stale connections (e.g. Neon auto-suspend) and reconnects
# transparently, preventing "connection is closed" errors on cold-start requests.
# pool_recycle replaces connections before Neon's ~5 min auto-suspend window.
engine = create_async_engine(
    settings.DATABASE_URL,
    pool_pre_ping=True,
    pool_recycle=240,
    echo=settings.DATABASE_ECHO,
)

# Async session factory
AsyncSessionLocal = async_sessionmaker(
    engine, class_=AsyncSession, expire_on_commit=False
)


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    async with AsyncSessionLocal() as session:
        yield session


async def init_db() -> None:
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


async def drop_db() -> None:
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
