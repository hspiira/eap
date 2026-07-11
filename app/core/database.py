"""
Database Configuration

Async SQLAlchemy setup for FastAPI application.
"""

from collections.abc import AsyncGenerator

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.core.config import settings
from app.infrastructure.models.base import Base

_is_sqlite = "sqlite" in settings.DATABASE_URL

# Create async engine.
# pool_pre_ping detects stale connections (e.g. Neon auto-suspend) and reconnects
# before handing the connection to the application, preventing "connection is closed"
# errors on the first request after a period of inactivity.
engine = create_async_engine(
    settings.DATABASE_URL,
    connect_args={"check_same_thread": False} if _is_sqlite else {},
    pool_pre_ping=True,
    # Recycle connections after 4 min so they are replaced before Neon's ~5 min
    # auto-suspend window makes them stale. Not applicable to SQLite.
    **({} if _is_sqlite else {"pool_recycle": 240}),
    echo=settings.DATABASE_ECHO,
)

# Async session factory
AsyncSessionLocal = async_sessionmaker(
    engine, class_=AsyncSession, expire_on_commit=False
)


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """
    Dependency for FastAPI to get async database session.
    
    Usage:
        @app.get("/items")
        async def get_items(db: AsyncSession = Depends(get_db)):
            ...
    """
    async with AsyncSessionLocal() as session:
            yield session


async def init_db() -> None:
    """
    Initialize database - create all tables.
    
    Call this on application startup.
    """
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


async def drop_db() -> None:
    """
    Drop all tables (use with caution!).
    """
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
