"""
Middleware setup for the FastAPI application.

Centralizes all middleware registration so main.py stays minimal.
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings
from app.shared.middleware.rate_limit import RateLimitConfig, RateLimitMiddleware


def setup_middleware(app: FastAPI) -> None:
    """Register all middleware on the FastAPI app. Order: first added = outermost (last to run)."""
    # Rate limiting (only in non-development)
    if not settings.is_development:
        app.add_middleware(
            RateLimitMiddleware,
            config=RateLimitConfig(
                requests_per_minute=60,
                requests_per_hour=1000,
                burst_size=10,
            ),
        )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins_list,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
