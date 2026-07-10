"""
Unit tests for the typed-exception hierarchy.

Phase 0 #C11 (SAD §13.2 / ADR-006): each domain exception class carries
its own HTTP status. The string-parsing utility `get_error_status_code`
has been removed; this test guards against any regression.
"""

import pytest

from app.domain.exceptions import (
    AuthenticationException,
    AuthorizationException,
    ConflictError,
    DomainError,
    EvexiaException,
    InvalidStateError,
    NotFoundError,
    PermissionDeniedError,
    ResourceNotFoundException,
    SubscriptionLimitError,
    TenantNotFoundException,
    ValidationException,
)


class TestExceptionHttpStatuses:
    @pytest.mark.parametrize(
        "exc_factory,expected_status",
        [
            (lambda: DomainError("rule violated"), 400),
            (lambda: NotFoundError("client missing"), 404),
            (lambda: ConflictError("already active"), 409),
            (lambda: InvalidStateError("cannot terminate draft"), 400),
            (lambda: ValidationException("bad input"), 422),
            (lambda: AuthenticationException(), 401),
            (lambda: AuthorizationException("client", "delete"), 403),
            (lambda: PermissionDeniedError(), 403),
            (lambda: TenantNotFoundException("t-123"), 404),
            (lambda: ResourceNotFoundException("client", "c-1"), 404),
            (lambda: SubscriptionLimitError(), 402),
        ],
    )
    def test_exception_carries_correct_http_status(self, exc_factory, expected_status):
        exc = exc_factory()
        assert isinstance(exc, EvexiaException)
        assert exc.http_status == expected_status

    def test_no_string_parser_exists(self):
        """Regression guard: removing the parser is part of the contract."""
        with pytest.raises(ImportError):
            from app.shared.utils.http_errors import get_error_status_code  # noqa: F401

    def test_typed_subclasses_carry_details(self):
        exc = NotFoundError(
            "Client not found",
            resource_type="Client",
            resource_id="c-123",
        )
        assert exc.details == {"resource_type": "Client", "resource_id": "c-123"}
        assert exc.error_code == "NOT_FOUND"

        exc = ConflictError("Duplicate name", details={"name": "ACME"})
        assert exc.details == {"name": "ACME"}
        assert exc.error_code == "CONFLICT"

    def test_to_api_response_shape(self):
        exc = NotFoundError("not here", resource_type="Client", resource_id="c-9")
        body = exc.to_api_response(path="/clients/c-9", request_id="req-1")
        assert body["error"] == "NOT_FOUND"
        assert body["message"] == "not here"
        assert body["path"] == "/clients/c-9"
        assert body["request_id"] == "req-1"
        # details list is built from the details dict
        assert body["details"]
        fields = {d["field"] for d in body["details"]}
        assert {"resource_type", "resource_id"}.issubset(fields)
