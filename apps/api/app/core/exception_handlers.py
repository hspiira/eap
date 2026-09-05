"""Exception handlers for the FastAPI application."""

import logging
from collections.abc import Iterable, Mapping, Sequence
from typing import Any

from fastapi import FastAPI, Request, status
from fastapi.exceptions import HTTPException, RequestValidationError
from fastapi.responses import JSONResponse
from pydantic import ValidationError

from app.domain.exceptions import EvexiaException
from app.shared.utils.errors import create_error_response

logger = logging.getLogger(__name__)

_STATUS_TO_ERROR_CODE: dict[int, str] = {
    status.HTTP_400_BAD_REQUEST: "BAD_REQUEST",
    status.HTTP_401_UNAUTHORIZED: "UNAUTHORIZED",
    status.HTTP_403_FORBIDDEN: "FORBIDDEN",
    status.HTTP_404_NOT_FOUND: "NOT_FOUND",
    status.HTTP_409_CONFLICT: "CONFLICT",
    status.HTTP_422_UNPROCESSABLE_CONTENT: "VALIDATION_ERROR",
    status.HTTP_429_TOO_MANY_REQUESTS: "RATE_LIMIT_EXCEEDED",
}


def _http_exception_message(detail: Any) -> str:
    if isinstance(detail, str):
        return detail
    if isinstance(detail, list) and detail:
        first = detail[0]
        if isinstance(first, dict) and "msg" in first:
            return str(first["msg"])
        return str(first)
    return "An error occurred"


_REQUEST_LOCATIONS = frozenset({"body", "query", "path", "header", "cookie"})


def _field_path(loc: Sequence[Any]) -> str | None:
    """Return the dotted field path for a Pydantic error location.

    Returns None when the error applies to the whole request body rather than a field.
    """
    parts = list(loc)
    if parts and parts[0] in _REQUEST_LOCATIONS:
        parts = parts[1:]
    return ".".join(str(part) for part in parts) or None


def _validation_details(errors: Iterable[Mapping[str, Any]]) -> list[dict[str, Any]]:
    """Convert Pydantic errors into error response details."""
    return [
        {
            "field": _field_path(error.get("loc", ())),
            "message": str(error.get("msg", "Invalid value")),
            "code": error.get("type"),
        }
        for error in errors
    ]


def _validation_message(details: Sequence[Mapping[str, Any]]) -> str:
    """Summarise validation failures for clients that do not read the details list."""
    if not details:
        return "Request validation failed"
    if len(details) == 1:
        field = details[0].get("field")
        message = details[0]["message"]
        return f"{field}: {message}" if field else str(message)
    named = [str(d["field"]) for d in details if d.get("field")]
    if named:
        return f"Validation failed for {len(details)} fields: {', '.join(named)}"
    return f"Validation failed with {len(details)} errors"


def register_exception_handlers(app: FastAPI) -> None:
    """Register all exception handlers on the FastAPI app."""

    def _request_id(request: Request) -> str | None:
        return getattr(request.state, "request_id", None)

    @app.exception_handler(HTTPException)
    async def http_exception_handler(request: Request, exc: HTTPException):
        error_code = _STATUS_TO_ERROR_CODE.get(exc.status_code, "HTTP_ERROR")
        message = _http_exception_message(exc.detail)
        path = str(request.url.path)
        content = create_error_response(
            error=error_code,
            message=message,
            path=path,
            request_id=_request_id(request),
        )
        headers = {"WWW-Authenticate": "Bearer"} if exc.status_code == 401 else None
        return JSONResponse(
            status_code=exc.status_code,
            content=content,
            headers=headers,
        )

    @app.exception_handler(EvexiaException)
    async def evexia_exception_handler(request: Request, exc: EvexiaException):
        path = str(request.url.path)
        content = exc.to_api_response(path=path, request_id=_request_id(request))
        headers = {"WWW-Authenticate": "Bearer"} if exc.http_status == 401 else None
        return JSONResponse(
            status_code=exc.http_status,
            content=content,
            headers=headers,
        )

    @app.exception_handler(RequestValidationError)
    async def request_validation_error_handler(request: Request, exc: RequestValidationError):
        details = _validation_details(exc.errors())
        return JSONResponse(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            content=create_error_response(
                error="VALIDATION_ERROR",
                message=_validation_message(details),
                details=details,
                path=str(request.url.path),
                request_id=_request_id(request),
            ),
        )

    @app.exception_handler(ValidationError)
    async def pydantic_validation_error_handler(request: Request, exc: ValidationError):
        details = _validation_details(exc.errors())
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content=create_error_response(
                error="VALIDATION_ERROR",
                message=_validation_message(details),
                details=details,
                path=str(request.url.path),
                request_id=_request_id(request),
            ),
        )

    @app.exception_handler(ValueError)
    async def value_error_handler(request: Request, exc: ValueError):
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content=create_error_response(
                error="VALUE_ERROR",
                message=str(exc),
                path=str(request.url.path),
                request_id=_request_id(request),
            ),
        )

    @app.exception_handler(Exception)
    async def general_exception_handler(request: Request, exc: Exception):
        logger.exception(f"Unhandled exception: {exc}")
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content=create_error_response(
                error="INTERNAL_ERROR",
                message="An internal server error occurred",
                path=str(request.url.path),
                request_id=_request_id(request),
            ),
        )
