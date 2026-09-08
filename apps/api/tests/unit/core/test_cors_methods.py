"""CORS must allow every verb the router serves.

TestClient and curl do not preflight, so a missing verb passes every other test
while no browser can reach the route.
"""

from app.main import app

_IMPLICIT = {"HEAD", "OPTIONS"}


def _cors_allowed_methods() -> set[str]:
    for middleware in app.user_middleware:
        if middleware.cls.__name__ == "CORSMiddleware":
            return set(middleware.kwargs["allow_methods"])
    raise AssertionError("CORSMiddleware is not installed")


def _router_methods() -> set[str]:
    schema = app.openapi()
    methods = {verb.upper() for path in schema["paths"].values() for verb in path}
    return methods - _IMPLICIT


class TestCorsMethods:
    def test_every_verb_the_router_serves_is_allowed_by_cors(self):
        missing = _router_methods() - _cors_allowed_methods()
        assert not missing, f"CORS would reject a preflight for {sorted(missing)}."

    def test_the_router_actually_serves_put(self):
        assert "PUT" in _router_methods()
