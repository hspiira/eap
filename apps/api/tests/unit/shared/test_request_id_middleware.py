"""RequestIdMiddleware + correlation context tests (Cross-cutting #Observability)."""

import re
import uuid

import pytest
from starlette.applications import Starlette
from starlette.requests import Request
from starlette.responses import JSONResponse
from starlette.routing import Route
from starlette.testclient import TestClient

from app.shared.middleware.request_id import (
    HEADER_NAME,
    RequestIdMiddleware,
    get_current_request_id,
)

_UUID_RE = re.compile(
    r"^[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-"
    r"[0-9a-fA-F]{4}-[0-9a-fA-F]{12}$"
)


def _build_app() -> Starlette:
    async def echo(request: Request):
        # Read the id via the contextvar to verify the binding works inside handlers.
        return JSONResponse(
            {
                "from_state": getattr(request.state, "request_id", None),
                "from_context": get_current_request_id(),
            }
        )

    app = Starlette(routes=[Route("/echo", echo)])
    app.add_middleware(RequestIdMiddleware)
    return app


@pytest.fixture
def client() -> TestClient:
    return TestClient(_build_app())


class TestRequestIdGeneration:
    def test_generates_uuid_when_no_header(self, client: TestClient):
        resp = client.get("/echo")
        body = resp.json()
        assert _UUID_RE.match(body["from_state"])
        assert body["from_state"] == body["from_context"]
        assert resp.headers[HEADER_NAME] == body["from_state"]

    def test_each_request_gets_a_distinct_id(self, client: TestClient):
        a = client.get("/echo").json()["from_state"]
        b = client.get("/echo").json()["from_state"]
        assert a != b


class TestInboundHeader:
    def test_canonical_uuid_is_honoured(self, client: TestClient):
        inbound = str(uuid.uuid4())
        resp = client.get("/echo", headers={HEADER_NAME: inbound})
        body = resp.json()
        assert body["from_state"] == inbound
        assert resp.headers[HEADER_NAME] == inbound

    def test_garbage_inbound_is_ignored(self, client: TestClient):
        resp = client.get("/echo", headers={HEADER_NAME: "not-a-uuid"})
        body = resp.json()
        assert body["from_state"] != "not-a-uuid"
        assert _UUID_RE.match(body["from_state"])

    def test_empty_inbound_is_ignored(self, client: TestClient):
        resp = client.get("/echo", headers={HEADER_NAME: ""})
        body = resp.json()
        assert _UUID_RE.match(body["from_state"])


class TestContextVarLifecycle:
    def test_context_var_unset_outside_request(self):
        # Outside an active middleware-bound request, the contextvar reads as None.
        assert get_current_request_id() is None

    def test_context_var_isolated_between_requests(self, client: TestClient):
        client.get("/echo")
        # After the request the contextvar in the test thread should still be None
        # because the middleware reset() it on exit.
        assert get_current_request_id() is None
