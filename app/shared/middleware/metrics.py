"""
Simple in-memory metrics for request count and error rate.

Exposed at GET /metrics as JSON. For Prometheus scraping, use a sidecar or
gateway that converts this JSON or instrument with prometheus_client.
"""

import time
from collections.abc import Callable
from typing import Any

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response


class MetricsMiddleware(BaseHTTPMiddleware):
    """
    Tracks total requests, 5xx count, and request latency in app.state.metrics.
    """

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        if not hasattr(request.app.state, "metrics"):
            request.app.state.metrics = {
                "request_count": 0,
                "error_5xx_count": 0,
                "start_time": time.monotonic(),
            }
        metrics = request.app.state.metrics
        metrics["request_count"] = metrics.get("request_count", 0) + 1
        start = time.perf_counter()
        response = await call_next(request)
        elapsed = time.perf_counter() - start
        if 500 <= response.status_code < 600:
            metrics["error_5xx_count"] = metrics.get("error_5xx_count", 0) + 1
        # Store last latency for simple exposure (optional)
        metrics["last_request_seconds"] = round(elapsed, 6)
        return response


def get_metrics(app_state: Any) -> dict[str, Any]:
    """Build metrics dict from app.state.metrics."""
    m = getattr(app_state, "metrics", None)
    if not m:
        return {
            "request_count": 0,
            "error_5xx_count": 0,
            "uptime_seconds": 0,
            "last_request_seconds": None,
        }
    uptime = time.monotonic() - m.get("start_time", time.monotonic())
    return {
        "request_count": m.get("request_count", 0),
        "error_5xx_count": m.get("error_5xx_count", 0),
        "uptime_seconds": round(uptime, 2),
        "last_request_seconds": m.get("last_request_seconds"),
    }
