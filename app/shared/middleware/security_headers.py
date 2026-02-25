"""
Security headers middleware.

Adds X-Frame-Options, X-Content-Type-Options, Referrer-Policy, optional
Strict-Transport-Security (HSTS), and optionally Content-Security-Policy-Report-Only
to all responses.
"""

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """Set security-related response headers on every response."""

    def __init__(
        self,
        app: object,
        x_frame_options: str = "DENY",
        csp_report_only: bool = False,
        csp_report_uri: str = "",
        hsts_max_age: int = 0,
    ) -> None:
        super().__init__(app)
        self.x_frame_options = x_frame_options
        self.csp_report_only = csp_report_only
        self.csp_report_uri = csp_report_uri
        self.hsts_max_age = hsts_max_age

    async def dispatch(self, request: Request, call_next: object):
        response = await call_next(request)
        response.headers["X-Frame-Options"] = self.x_frame_options
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        if self.hsts_max_age > 0:
            response.headers["Strict-Transport-Security"] = (
                f"max-age={self.hsts_max_age}; includeSubDomains"
            )
        if self.csp_report_only:
            directive = "default-src 'self'"
            if self.csp_report_uri:
                directive += f"; report-uri {self.csp_report_uri}"
            response.headers["Content-Security-Policy-Report-Only"] = directive
        return response
