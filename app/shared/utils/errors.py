"""
Standardized Error Response Utilities

Provides consistent error response format across all API endpoints.
"""

from datetime import UTC, datetime
from typing import Any

from pydantic import BaseModel, Field


class ErrorDetail(BaseModel):
    """Individual error detail."""

    field: str | None = Field(None, description="Field that caused the error")
    message: str = Field(..., description="Human-readable error message")
    code: str | None = Field(None, description="Machine-readable error code")


class ErrorResponse(BaseModel):
    """
    Standardized API error response.

    All API errors should use this format for consistency.
    """

    error: str = Field(..., description="Error type/code")
    message: str = Field(..., description="Human-readable error message")
    details: list[ErrorDetail] = Field(default_factory=list, description="Additional error details")
    timestamp: datetime = Field(
        default_factory=lambda: datetime.now(UTC),
        description="When the error occurred",
    )
    request_id: str | None = Field(None, description="Request tracking ID")
    path: str | None = Field(None, description="Request path that caused the error")

    model_config = {
        "json_schema_extra": {
            "example": {
                "error": "VALIDATION_ERROR",
                "message": "Invalid input data",
                "details": [
                    {
                        "field": "email",
                        "message": "Invalid email format",
                        "code": "INVALID_FORMAT",
                    }
                ],
                "timestamp": "2024-01-15T10:30:00Z",
                "request_id": "req-abc123",
                "path": "/users/",
            }
        }
    }


def create_error_response(
    error: str,
    message: str,
    details: list[dict[str, Any]] | None = None,
    request_id: str | None = None,
    path: str | None = None,
) -> dict[str, Any]:
    """
    Create a standardized error response dictionary.

    Args:
        error: Error type/code (e.g., "VALIDATION_ERROR", "NOT_FOUND")
        message: Human-readable error message
        details: Optional list of error details
        request_id: Optional request tracking ID
        path: Optional request path

    Returns:
        Dictionary suitable for JSONResponse
    """
    response = ErrorResponse(
        error=error,
        message=message,
        details=[ErrorDetail(**d) for d in (details or [])],
        request_id=request_id,
        path=path,
    )
    return response.model_dump(mode="json", exclude_none=True)
