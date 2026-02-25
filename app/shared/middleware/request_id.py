"""
Request ID middleware.

Sets a unique request_id on each request so error responses can include
a non-sensitive identifier for client-side logging and support.
"""

import uuid

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request


class RequestIdMiddleware(BaseHTTPMiddleware):
    """Set request.state.request_id for every request."""

    async def dispatch(self, request: Request, call_next: object):
        request.state.request_id = str(uuid.uuid4())
        return await call_next(request)
