"""
A tripwire for the fixture-backed endpoints.

The FE serves local fixtures for these resources and filters them in the browser.
That is correct only while the fixture returns the whole dataset as one page. The
moment one of these endpoints starts filtering server-side, the FE page must send
the params instead of filtering a page; otherwise it silently shows wrong counts
and hides matching rows on later pages, with no error anywhere.

So: when one of these gains a filter param, this test fails. It is not asking you
to keep them param-free. It is asking you to update the FE page in the same
change. Delete the entry here when you do.
"""

from app.main import app

# Endpoint -> the params it may have today. Anything beyond this is a filter.
PAGINATION_ONLY = {"tenant_id", "page", "limit", "sort_by", "sort_desc"}

FIXTURE_BACKED = {
    "/care-callback-campaigns": PAGINATION_ONLY,
    "/critical-incidents": PAGINATION_ONLY,
}


def _query_params(path: str) -> set[str]:
    """Read the published contract rather than the route table; routers are
    mounted, so app.routes does not carry them."""
    spec = app.openapi()["paths"].get(path)
    assert spec is not None, f"route not found in the OpenAPI schema: GET {path}"
    return {q["name"] for q in spec["get"].get("parameters", []) if q.get("in") == "query"}


class TestFixtureBackedEndpointsStillHaveNoFilters:
    def test_care_callback_campaigns(self) -> None:
        _assert_no_new_filters("/care-callback-campaigns")

    def test_critical_incidents(self) -> None:
        _assert_no_new_filters("/critical-incidents")


def _assert_no_new_filters(path: str) -> None:
    allowed = FIXTURE_BACKED[path]
    actual = _query_params(path)
    new = actual - allowed
    assert not new, (
        f"GET {path} gained query param(s) {sorted(new)}.\n"
        f"This endpoint is fixture-backed on the frontend, which filters the fetched "
        f"page in the browser. If it now filters server-side, the FE page must send "
        f"these params; otherwise its counts and pagination will be wrong (see "
        f"finding F1). Update the FE page, then remove this endpoint from "
        f"FIXTURE_BACKED."
    )
