"""
Exception handlers for the FastAPI application.

Register all domain and global exception handlers in one place.
"""

import logging

from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse

from app.domain.exceptions import EvexiaException
from app.shared.utils.errors import create_error_response

logger = logging.getLogger(__name__)


def register_exception_handlers(app: FastAPI) -> None:
    """Register all exception handlers on the FastAPI app."""

    @app.exception_handler(EvexiaException)
    async def evexia_exception_handler(request: Request, exc: EvexiaException):
        path = str(request.url.path)
        content = exc.to_api_response(path=path)
        headers = {"WWW-Authenticate": "Bearer"} if exc.http_status == 401 else None
        return JSONResponse(
            status_code=exc.http_status,
            content=content,
            headers=headers,
        )

    @app.exception_handler(ValueError)
    async def value_error_handler(request: Request, exc: ValueError):
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content=create_error_response(
                error="VALUE_ERROR",
                message=str(exc),
                path=str(request.url.path),
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
            ),
        )
