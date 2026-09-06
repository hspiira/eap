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


class TestFieldErrorsReachTheirField:
    """A field error must name the input it is about.

    ValidationException carried its field as details={"field": field}, and the
    serialiser reads details keys as field names, so every such error arrived
    against a field literally called "field" with a field name for a message.
    No client could attach it to the input it described.
    """

    def test_a_validation_error_names_the_real_field(self):
        error = ValidationException("Delivery context is required", field="delivery_context")

        details = error.to_api_response()["details"]

        assert details == [
            {
                "field": "delivery_context",
                "message": "Delivery context is required",
                "code": None,
            }
        ]

    def test_a_validation_error_can_carry_a_machine_readable_code(self):
        error = ValidationException("Bad code", field="code", code="invalid_client_code")

        assert error.to_api_response()["details"][0]["code"] == "invalid_client_code"

    def test_a_validation_error_without_a_field_has_no_details(self):
        body = ValidationException("Something is wrong").to_api_response()

        assert "details" not in body
        assert body["message"] == "Something is wrong"

    def test_field_errors_may_repeat_a_field_which_a_details_dict_cannot(self):
        error = DomainError(
            "Provider is not eligible",
            field_errors=[
                {"field": "eligibility", "message": "Panel status is Suspended", "code": "panel"},
                {"field": "eligibility", "message": "Accreditation lapsed", "code": "accred"},
            ],
        )

        details = error.to_api_response()["details"]

        assert [d["code"] for d in details] == ["panel", "accred"]

    def test_a_plain_details_dict_is_unchanged(self):
        """Errors that never asked for codes must serialise as they always did."""
        error = DomainError("x", details={"resource_id": "abc"})

        assert error.to_api_response()["details"] == [
            {"field": "resource_id", "message": "abc", "code": None}
        ]
