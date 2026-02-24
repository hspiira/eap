"""
Middleware setup for the FastAPI application.

Centralizes all middleware registration so main.py stays minimal.
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings
from app.shared.middleware.rate_limit import RateLimitConfig, RateLimitMiddleware
from app.shared.middleware.request_size import RequestSizeLimitMiddleware


# Max request body size (10MB). Document in README or docs.
MAX_REQUEST_BODY_BYTES = 10 * 1024 * 1024


def setup_middleware(app: FastAPI) -> None:
    """Register all middleware on the FastAPI app. Order: first added = outermost (last to run)."""
    # Request body size limit (reject large payloads before reading)
    app.add_middleware(RequestSizeLimitMiddleware, max_bytes=MAX_REQUEST_BODY_BYTES)

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
