"""Viewers are read-only, and that is enforced once rather than route by route.

SEC-04. `require_not_viewer` works but is opt-in, so the gate was only as good
as the memory of whoever added the last route. Scanning the built dependency
tree found 100 mutating routes that authenticated the caller and never checked
they could write, among them every DSAR mutation and every contract command.

Two tests hold this closed: one asserts the blanket gate refuses a Viewer on a
real request, the other asserts the allowlist has not quietly grown.
"""

import pytest
import pytest_asyncio
from fastapi import HTTPException
from fastapi.routing import APIRoute
from httpx import ASGITransport, AsyncClient

from app.core.authorization import UNSAFE_METHODS, VIEWER_WRITABLE, block_viewer_writes
from app.core.security import TokenData, get_current_user, get_current_user_optional
from app.main import app

#: Gates that make a route's write permission explicit. `require_tenant_role`
#: and `require_self_or_role` are factories whose inner function is `_require`;
#: matching only the factory name undercounts the protected routes.
WRITE_GATES = {
    "require_not_viewer",
    "require_admin",
    "require_tenant_role",
    "require_self_or_role",
    "require_self_or_admin",
    "require_platform_admin",
    "require_platform_admin_if_configured",
    "_require",
}


def _api_routes(routes):
    for route in routes:
        if isinstance(route, APIRoute):
            yield route
        included = getattr(route, "original_router", None)
        if included is not None:
            yield from _api_routes(included.routes)


def _dependency_names(route: APIRoute) -> set[str]:
    names: set[str] = set()
    pending = list(route.dependant.dependencies)
    while pending:
        dependency = pending.pop()
        if dependency.call is not None:
            names.add(getattr(dependency.call, "__name__", ""))
        pending.extend(dependency.dependencies)
    return names


ROUTES = list(_api_routes(app.routes))
MUTATING = [
    (sorted(set(r.methods) & UNSAFE_METHODS)[0], r.path)
    for r in ROUTES
    if set(r.methods) & UNSAFE_METHODS
]


def test_the_scan_sees_the_whole_application():
    assert len(ROUTES) > 300
    assert len(MUTATING) > 150


def test_the_allowlist_only_names_routes_that_exist():
    """A stale entry silently re-opens a future route at the same path."""
    assert not sorted(set(VIEWER_WRITABLE) - set(MUTATING))


def test_the_allowlist_stays_small_and_argued_for():
    """Each entry carries its reason; growth has to be deliberate."""
    assert set(VIEWER_WRITABLE) == {
        ("POST", "/auth/login"),
        ("POST", "/auth/logout"),
        ("POST", "/auth/refresh"),
        ("POST", "/auth/set-initial-password"),
        ("POST", "/search"),
        ("POST", "/survey-campaigns/{campaign_id}/webhook"),
    }
    assert all(reason.strip() for reason in VIEWER_WRITABLE.values())


@pytest_asyncio.fixture
async def viewer_http():
    """The whole application, with the caller's role forced to Viewer.

    Through the real app rather than a probe: the gate is an app-level
    dependency, and the point of the test is that no route escapes it.
    """
    viewer = TokenData(user_id="u-1", tenant_id="t-1", role="Viewer")
    app.dependency_overrides[get_current_user_optional] = lambda: viewer
    app.dependency_overrides[get_current_user] = lambda: viewer
    try:
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as http:
            yield http
    finally:
        app.dependency_overrides.pop(get_current_user_optional, None)
        app.dependency_overrides.pop(get_current_user, None)


@pytest.mark.parametrize(
    ("method", "path"),
    [
        ("POST", "/contracts/c-1/terminate"),
        ("PATCH", "/contracts/c-1/pricing"),
        ("POST", "/dsar/export"),
        ("POST", "/dsar/req-1/execute-erasure"),
        ("PATCH", "/documents/doc-1/confidentiality"),
        ("POST", "/care-callback-campaigns/cmp-1/enrol"),
        ("POST", "/outreach-records/out-1/escalate"),
        ("POST", "/reports/templates/tpl-1/run"),
    ],
    ids=lambda value: str(value).strip("/").replace("/", "-"),
)
async def test_a_viewer_is_refused_on_a_real_request(viewer_http, method, path):
    """None of these carried a write gate of their own before SEC-04."""
    response = await viewer_http.request(method, path, json={})
    assert response.status_code == 403, response.text
    assert "read-only" in response.text.lower()


async def test_an_allowlisted_route_gets_past_the_gate(viewer_http):
    """Refused at validation, not at the gate: a Viewer may still search."""
    response = await viewer_http.post("/search?tenant_id=t-1", json={})
    assert response.status_code != 403, response.text


def test_the_routes_that_still_rely_only_on_the_blanket_gate_are_visible():
    """Not a failure: a record of which routes have no gate of their own.

    100 mutating routes reach a Viewer only because the blanket gate stops
    them. Giving each its own explicit role is follow-up work; this asserts the
    number does not grow while that is outstanding.
    """
    relying = [
        r
        for r in ROUTES
        if set(r.methods) & UNSAFE_METHODS and not (_dependency_names(r) & WRITE_GATES)
    ]
    assert len(relying) <= 100


class _StubRequest:
    """Only what the guard reads: the method and the matched route template."""

    def __init__(self, method: str, path: str):
        self.method = method
        self.scope = {"route": type("R", (), {"path": path})()}
        self.url = type("U", (), {"path": path})()


def _viewer(role: str = "Viewer") -> TokenData:
    return TokenData(user_id="u-1", tenant_id="t-1", role=role)


class TestTheGateRefusesAViewer:
    @pytest.mark.parametrize(
        ("method", "path"),
        [
            ("POST", "/contracts/{contract_id}/terminate"),
            ("PATCH", "/contracts/{contract_id}/pricing"),
            ("POST", "/dsar/{request_id}/execute-erasure"),
            ("POST", "/documents/{document_id}/publish"),
            ("DELETE", "/members/{member_id}/account"),
        ],
    )
    async def test_an_unsafe_method_is_refused(self, method, path):
        with pytest.raises(HTTPException) as refused:
            await block_viewer_writes(_StubRequest(method, path), _viewer())
        assert refused.value.status_code == 403
        assert "read-only" in refused.value.detail.lower()

    async def test_an_allowlisted_route_still_works_for_a_viewer(self):
        """A Viewer has to be able to search, and to end their own session."""
        await block_viewer_writes(_StubRequest("POST", "/search"), _viewer())
        await block_viewer_writes(_StubRequest("POST", "/auth/logout"), _viewer())

    @pytest.mark.parametrize("role", ["Admin", "User"])
    async def test_the_gate_never_stops_a_role_that_may_write(self, role):
        """It must not become the reason an Admin's write fails."""
        await block_viewer_writes(
            _StubRequest("POST", "/contracts/{contract_id}/terminate"), _viewer(role)
        )

    async def test_a_read_is_untouched(self):
        await block_viewer_writes(_StubRequest("GET", "/contracts/{contract_id}"), _viewer())

    async def test_an_anonymous_request_is_left_to_the_route(self):
        """Whether a route may be called without a token is decided elsewhere."""
        await block_viewer_writes(_StubRequest("POST", "/auth/login"), None)
        await block_viewer_writes(_StubRequest("POST", "/contracts/"), None)
