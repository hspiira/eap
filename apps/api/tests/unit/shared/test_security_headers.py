"""
Cover for the security headers middleware.

The headers are the browser-side half of several controls, and each one is
conditional on configuration, so the off states matter as much as the on states.
"""

import pytest
from fastapi import FastAPI, HTTPException
from fastapi.testclient import TestClient

from app.core.exception_handlers import register_exception_handlers
from app.shared.middleware.request_id import RequestIdMiddleware
from app.shared.middleware.security_headers import SecurityHeadersMiddleware


def _client(**middleware_kwargs: object) -> TestClient:
    app = FastAPI()
    app.add_middleware(SecurityHeadersMiddleware, **middleware_kwargs)
    register_exception_handlers(app)

    @app.get("/ok")
    async def ok() -> dict[str, bool]:
        return {"ok": True}

    @app.get("/refused")
    async def refused() -> dict[str, bool]:
        raise HTTPException(status_code=403, detail="nope")

    @app.get("/unhandled")
    async def unhandled() -> dict[str, bool]:
        raise RuntimeError("deliberate")

    return TestClient(app, raise_server_exceptions=False)


class TestAlwaysPresent:
    def test_frame_options_defaults_to_deny(self) -> None:
        response = _client().get("/ok")
        assert response.headers["X-Frame-Options"] == "DENY"

    def test_content_type_options_is_nosniff(self) -> None:
        response = _client().get("/ok")
        assert response.headers["X-Content-Type-Options"] == "nosniff"

    def test_referrer_policy(self) -> None:
        response = _client().get("/ok")
        assert response.headers["Referrer-Policy"] == "strict-origin-when-cross-origin"

    def test_frame_options_is_configurable(self) -> None:
        response = _client(x_frame_options="SAMEORIGIN").get("/ok")
        assert response.headers["X-Frame-Options"] == "SAMEORIGIN"


class TestStrictTransportSecurity:
    def test_absent_when_max_age_is_zero(self) -> None:
        response = _client().get("/ok")
        assert "Strict-Transport-Security" not in response.headers

    def test_present_with_subdomains_when_configured(self) -> None:
        response = _client(hsts_max_age=31536000).get("/ok")
        assert (
            response.headers["Strict-Transport-Security"] == "max-age=31536000; includeSubDomains"
        )


class TestContentSecurityPolicy:
    def test_absent_by_default(self) -> None:
        response = _client().get("/ok")
        assert "Content-Security-Policy-Report-Only" not in response.headers

    def test_report_only_without_a_uri(self) -> None:
        response = _client(csp_report_only=True).get("/ok")
        assert response.headers["Content-Security-Policy-Report-Only"] == "default-src 'self'"

    def test_report_only_with_a_uri(self) -> None:
        response = _client(csp_report_only=True, csp_report_uri="/csp-report").get("/ok")
        assert (
            response.headers["Content-Security-Policy-Report-Only"]
            == "default-src 'self'; report-uri /csp-report"
        )

    def test_enforcing_policy_is_never_set(self) -> None:
        """Only the report-only variant is implemented; assert we do not enforce."""
        response = _client(csp_report_only=True, csp_report_uri="/csp-report").get("/ok")
        assert "Content-Security-Policy" not in response.headers


class TestErrorResponses:
    """Error responses must carry the headers too, not just successful ones."""

    @pytest.mark.parametrize(
        "header",
        ["X-Frame-Options", "X-Content-Type-Options", "Referrer-Policy"],
    )
    def test_headers_are_present_on_a_handled_error(self, header: str) -> None:
        response = _client().get("/refused")
        assert response.status_code == 403
        assert header in response.headers

    def test_headers_are_present_on_a_404(self) -> None:
        response = _client().get("/does-not-exist")
        assert response.status_code == 404
        assert response.headers["X-Content-Type-Options"] == "nosniff"

    def test_hsts_is_present_on_an_error_when_configured(self) -> None:
        response = _client(hsts_max_age=600).get("/refused")
        assert response.headers["Strict-Transport-Security"] == "max-age=600; includeSubDomains"


def _client_with_request_id() -> TestClient:
    """Mirrors the real app, which mounts both middlewares in setup_middleware."""
    app = FastAPI()
    app.add_middleware(SecurityHeadersMiddleware)
    app.add_middleware(RequestIdMiddleware)
    register_exception_handlers(app)

    @app.get("/unhandled")
    async def unhandled() -> dict[str, bool]:
        raise RuntimeError("deliberate")

    return TestClient(app, raise_server_exceptions=False)


class TestFiveHundredBypassesTheStack:
    """Documents the gap in BE-A07 rather than the behaviour we want.

    FastAPI installs the catch-all `Exception` handler as ServerErrorMiddleware's
    handler, and that middleware is the outermost layer, so a 500 produced there
    never travels back out through anything added with `add_middleware`. These
    assertions are deliberately inverted: they pin the current behaviour so the
    gap is visible in the suite, and they will fail when BE-A07 is fixed, which
    is the reminder to invert them.
    """

    @pytest.mark.parametrize(
        "header",
        ["X-Frame-Options", "X-Content-Type-Options", "Referrer-Policy"],
    )
    def test_headers_are_absent_on_an_unhandled_exception(self, header: str) -> None:
        response = _client().get("/unhandled")
        assert response.status_code == 500
        assert header not in response.headers

    def test_the_error_envelope_is_still_correct(self) -> None:
        """The handler itself works; only the headers are lost."""
        response = _client().get("/unhandled")
        body = response.json()
        assert body["error"] == "INTERNAL_ERROR"
        assert body["message"] == "An internal server error occurred"

    def test_the_request_id_survives_in_the_body(self) -> None:
        """Correlation is half lost: body keeps the id, the header does not."""
        response = _client_with_request_id().get("/unhandled")
        assert response.json()["request_id"]
        assert "X-Request-ID" not in response.headers
