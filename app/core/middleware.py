"""
Middleware setup for the FastAPI application.

Centralizes all middleware registration so main.py stays minimal.
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings
from app.shared.middleware.metrics import MetricsMiddleware
from app.shared.middleware.rate_limit import RateLimitConfig, RateLimitMiddleware
from app.shared.middleware.request_id import RequestIdMiddleware
from app.shared.middleware.request_size import RequestSizeLimitMiddleware
from app.shared.middleware.security_headers import SecurityHeadersMiddleware


# Max request body size (10MB). Document in README or docs.
MAX_REQUEST_BODY_BYTES = 10 * 1024 * 1024


def setup_middleware(app: FastAPI) -> None:
    """Register all middleware on the FastAPI app. Order: first added = outermost (last to run)."""
    app.add_middleware(RequestIdMiddleware)
    hsts_max_age = 0
    if getattr(settings, "ENVIRONMENT", "") == "production":
        hsts_max_age = getattr(
            settings, "SECURITY_HEADERS_HSTS_MAX_AGE", 31536000
        )
    app.add_middleware(
        SecurityHeadersMiddleware,
        x_frame_options=getattr(
            settings, "SECURITY_HEADERS_X_FRAME_OPTIONS", "DENY"
        ),
        csp_report_only=getattr(
            settings, "SECURITY_HEADERS_CSP_REPORT_ONLY", False
        ),
        csp_report_uri=getattr(
            settings, "SECURITY_HEADERS_CSP_REPORT_URI", ""
        ),
        hsts_max_age=hsts_max_age,
    )
    # Metrics (request count, 5xx count, latency) for GET /metrics
    app.add_middleware(MetricsMiddleware)
    # Request body size limit (reject large payloads before reading)
    app.add_middleware(RequestSizeLimitMiddleware, max_bytes=MAX_REQUEST_BODY_BYTES)

    # Rate limiting (always on; 5x higher in development; very high in test so E2E won't 429)
    rate_per_min = getattr(
        settings, "RATE_LIMIT_REQUESTS_PER_MINUTE", 60
    )
    rate_per_hour = getattr(
        settings, "RATE_LIMIT_REQUESTS_PER_HOUR", 1000
    )
    if getattr(settings, "ENVIRONMENT", "") == "test":
        rate_per_min = 10_000
        rate_per_hour = 100_000
    elif settings.is_development:
        rate_per_min = rate_per_min * 5
        rate_per_hour = rate_per_hour * 5
    app.add_middleware(
        RateLimitMiddleware,
        config=RateLimitConfig(
            requests_per_minute=rate_per_min,
            requests_per_hour=rate_per_hour,
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
