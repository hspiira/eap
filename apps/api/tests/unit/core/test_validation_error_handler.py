"""Validation error handler tests.

Validation failures must arrive as `details[{field, message, code}]`, which is the shape
the web client reads in apps/web/src/api/errors.ts to attach errors to form fields.
"""

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from pydantic import BaseModel, Field

from app.core.exception_handlers import (
    _field_path,
    _validation_message,
    register_exception_handlers,
)


class Contact(BaseModel):
    email: str


class Signup(BaseModel):
    name: str = Field(min_length=2)
    secret: str = Field(min_length=32)
    contact: Contact


@pytest.fixture
def client() -> TestClient:
    app = FastAPI()
    register_exception_handlers(app)

    @app.post("/signup")
    async def signup(body: Signup) -> dict[str, bool]:
        return {"ok": True}

    @app.get("/items")
    async def items(limit: int) -> dict[str, int]:
        return {"limit": limit}

    return TestClient(app, raise_server_exceptions=False)


def extract_field_errors(body: dict) -> dict[str, str]:
    """Mirror of normalizeFieldErrorsBody in apps/web/src/api/errors.ts."""
    details = body.get("details")
    if not isinstance(details, list):
        return {}
    return {
        str(d["field"]): d["message"] for d in details if isinstance(d, dict) and d.get("field")
    }


class TestFieldPath:
    @pytest.mark.parametrize(
        ("loc", "expected"),
        [
            (["body", "secret"], "secret"),
            (["body", "contact", "email"], "contact.email"),
            (["body", "items", 0, "name"], "items.0.name"),
            (["query", "limit"], "limit"),
            (["path", "client_id"], "client_id"),
            (["name"], "name"),
            (["body"], None),
            ([], None),
        ],
    )
    def test_strips_the_request_location_and_joins_the_rest(self, loc, expected):
        assert _field_path(loc) == expected


class TestValidationMessage:
    def test_names_the_field_for_a_single_error(self):
        details = [{"field": "secret", "message": "Field required"}]
        assert _validation_message(details) == "secret: Field required"

    def test_omits_the_field_when_the_error_has_none(self):
        details = [{"field": None, "message": "Input should be an object"}]
        assert _validation_message(details) == "Input should be an object"

    def test_lists_the_fields_when_several_fail(self):
        details = [
            {"field": "name", "message": "too short"},
            {"field": "secret", "message": "Field required"},
        ]
        assert _validation_message(details) == "Validation failed for 2 fields: name, secret"

    def test_falls_back_when_there_are_no_details(self):
        assert _validation_message([]) == "Request validation failed"


class TestRequestValidation:
    def test_returns_the_standard_error_envelope(self, client: TestClient):
        response = client.post("/signup", json={})

        assert response.status_code == 422
        body = response.json()
        assert body["error"] == "VALIDATION_ERROR"
        assert body["path"] == "/signup"
        assert isinstance(body["details"], list)

    def test_reports_every_failing_field_with_a_code(self, client: TestClient):
        response = client.post("/signup", json={"name": "x", "contact": {}})

        assert extract_field_errors(response.json()) == {
            "name": "String should have at least 2 characters",
            "secret": "Field required",
            "contact.email": "Field required",
        }
        codes = {d["field"]: d["code"] for d in response.json()["details"]}
        assert codes["name"] == "string_too_short"
        assert codes["secret"] == "missing"

    def test_maps_query_parameters_to_their_bare_name(self, client: TestClient):
        response = client.get("/items")

        assert response.status_code == 422
        assert extract_field_errors(response.json()) == {"limit": "Field required"}

    def test_omits_field_when_the_whole_body_is_wrong(self, client: TestClient):
        response = client.post("/signup", json=[1, 2, 3])

        assert response.status_code == 422
        body = response.json()
        assert extract_field_errors(body) == {}
        assert "field" not in body["details"][0]
        assert body["message"]

    def test_accepts_a_valid_payload(self, client: TestClient):
        response = client.post(
            "/signup",
            json={"name": "Ada", "secret": "a" * 32, "contact": {"email": "a@b.co"}},
        )

        assert response.status_code == 200
