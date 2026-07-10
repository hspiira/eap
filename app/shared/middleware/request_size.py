"""
Request body size limit middleware.

Rejects requests with Content-Length over the configured limit (e.g. 10MB)
to mitigate DoS via large payloads. Applied before the body is read.
"""

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse


class RequestSizeLimitMiddleware(BaseHTTPMiddleware):
    """Reject requests whose Content-Length exceeds max_bytes (default 10MB)."""

    def __init__(self, app: object, max_bytes: int = 10 * 1024 * 1024) -> None:
        super().__init__(app)
        self.max_bytes = max_bytes

    async def dispatch(self, request: Request, call_next: object):
        content_length = request.headers.get("content-length")
        if content_length is not None:
            try:
                size = int(content_length)
                if size > self.max_bytes:
                    return JSONResponse(
                        status_code=413,
                        content={
                            "error": "REQUEST_ENTITY_TOO_LARGE",
                            "message": f"Request body must not exceed {self.max_bytes // (1024 * 1024)}MB",
                        },
                    )
            except ValueError:
                pass  # Invalid Content-Length; let the app handle it
        return await call_next(request)
