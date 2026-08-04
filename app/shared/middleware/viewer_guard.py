"""
Viewer Guard Middleware

Blocks Viewer-role users from all mutation endpoints (POST, PATCH, PUT, DELETE).
The role is read from the JWT claim embedded at token-mint time, so no DB
round-trip is required.

Auth routes (/auth/*) are exempt — they are public by design.
"""

import logging

from fastapi import Request
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp

logger = logging.getLogger(__name__)

_MUTATION_METHODS = frozenset({"POST", "PATCH", "PUT", "DELETE"})
_EXEMPT_PATH_PREFIXES = ("/auth/",)
_VIEWER_ROLE = "VIEWER"


class ViewerGuardMiddleware(BaseHTTPMiddleware):
    def __init__(self, app: ASGIApp) -> None:
        super().__init__(app)

    async def dispatch(self, request: Request, call_next):
        if request.method not in _MUTATION_METHODS:
            return await call_next(request)

        path = request.url.path
        if any(path.startswith(p) for p in _EXEMPT_PATH_PREFIXES):
            return await call_next(request)

        auth = request.headers.get("authorization", "")
        if not auth.lower().startswith("bearer "):
            return await call_next(request)

        token = auth.split(" ", 1)[1]
        try:
            from app.core.security import decode_token

            token_data = decode_token(token)
            if token_data.role == _VIEWER_ROLE:
                return JSONResponse(
                    status_code=403,
                    content={
                        "detail": "Insufficient role: Viewers cannot perform write operations"
                    },
                )
        except Exception:
            # Fail open by design: an undecodable token is not this guard's problem —
            # the auth dependency rejects it downstream. Logged so a decode regression
            # here (which would silently disable the viewer guard) is visible.
            logger.debug(
                "viewer_guard: token decode failed; deferring to auth dependency",
                exc_info=True,
            )

        return await call_next(request)
