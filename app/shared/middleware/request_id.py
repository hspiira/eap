"""
Request ID / correlation middleware (SAD §8.3 — observability).

Sets a unique request id per request so:
  * error responses can include a non-sensitive correlation id;
  * clients (or upstream proxies) can supply ``X-Request-Id`` to stitch their
    traces to ours — we honour the inbound value when it's a canonical UUID;
  * structured logs anywhere in the request (route, use case, repo) can read
    the id via the ``current_request_id`` context variable;
  * the response carries ``X-Request-Id`` so the client can echo it on retry.
"""

import contextvars
import re
import uuid

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

HEADER_NAME = "X-Request-Id"

_UUID_RE = re.compile(
    r"^[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-"
    r"[0-9a-fA-F]{4}-[0-9a-fA-F]{12}$"
)
"""Inbound IDs must be canonical UUIDs; otherwise we generate fresh ones so
log correlation can't be spoofed with junk."""


current_request_id: contextvars.ContextVar[str | None] = contextvars.ContextVar(
    "current_request_id", default=None
)


def get_current_request_id() -> str | None:
    """Read the request id bound for the active task — ``None`` outside a request."""
    return current_request_id.get()


class RequestIdMiddleware(BaseHTTPMiddleware):
    """Bind request_id on ``request.state``, the logging context, and the response."""

    async def dispatch(self, request: Request, call_next):
        inbound = request.headers.get(HEADER_NAME)
        request_id = (
            inbound if inbound and _UUID_RE.match(inbound) else str(uuid.uuid4())
        )
        request.state.request_id = request_id
        token = current_request_id.set(request_id)
        try:
            response: Response = await call_next(request)
        finally:
            current_request_id.reset(token)
        response.headers[HEADER_NAME] = request_id
        return response
