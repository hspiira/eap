"""
Database Configuration

SQLAlchemy setup for FastAPI application.
"""

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from app.infrastructure.models.base import Base


# Database URL - should come from config
DATABASE_URL = "sqlite:///./eap.db"  # TODO: Move to config


# Create engine
engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False} if "sqlite" in DATABASE_URL else {},
    echo=False  # Set to True for SQL query logging
)


# Session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def get_db() -> Session:
    """
    Dependency for FastAPI to get database session.
    
    Usage:
        @app.get("/items")
        def get_items(db: Session = Depends(get_db)):
            ...
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db() -> None:
    """
    Initialize database - create all tables.
    
    Call this on application startup.
    """
    Base.metadata.create_all(bind=engine)


def drop_db() -> None:
    """
    Drop all tables (use with caution!).
    """
    Base.metadata.drop_all(bind=engine)
