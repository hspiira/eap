"""Every mounted route resolves a user, unless it is deliberately public.

SEC-01 recorded two report routes readable with no credentials. Scanning the
built dependency tree found twenty-six such routes, including care-callback
campaigns, outreach records, contacts, KPIs and service assignments: an
entity-ID read whose sibling list route was correctly guarded.

The allowlist below is the whole of the public surface. A new route that
resolves no user fails this test rather than shipping open, which is the
inventory SEC-01 and SEC-03 ask for, kept honest by CI instead of by review.
"""

from fastapi.routing import APIRoute

from app.main import app

#: Dependencies that put an authenticated user in scope.
AUTH_DEPENDENCIES = {
    "get_current_user",
    "get_current_active_user",
    "require_same_tenant",
    "require_admin",
    "require_not_viewer",
    "require_tenant_role",
    "require_clinical_scope",
    "require_scope",
    "require_self_or_admin",
    "require_platform_admin",
    "require_platform_admin_if_configured",
}

#: Routes that must stay reachable without a token, with the reason each one is.
INTENTIONALLY_PUBLIC = {
    ("GET", "/"): "landing page",
    ("GET", "/docs"): "API reference",
    ("GET", "/health"): "readiness probe",
    ("GET", "/metrics"): "metrics scrape",
    ("POST", "/auth/login"): "obtains the token",
    ("POST", "/auth/logout"): "clears a session that may already be invalid",
    ("POST", "/auth/refresh"): "exchanges a refresh token",
    ("POST", "/auth/set-initial-password"): "consumes a single-use invite token",
    ("GET", "/auth/azure/login"): "starts the SSO redirect",
    ("GET", "/auth/azure/callback"): "receives the SSO redirect",
    ("POST", "/survey-campaigns/{campaign_id}/webhook"): "signed provider webhook",
    ("GET", "/tenants/check-code/{code}"): "signup-time code availability",
    # Provider module, owned by the provider worktrees. Tracked, not approved:
    # see docs/reviews/MODULES_REPAIR_PLAN.md, stream 1 ownership block.
    ("GET", "/provider-specialties"): "PENDING: provider owner to gate this read",
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


def test_the_scan_sees_the_whole_application():
    """A broken walk would make every assertion below vacuous."""
    assert len(ROUTES) > 300


def test_no_route_is_reachable_without_a_user_unless_it_is_on_the_allowlist():
    open_routes = {
        (sorted(route.methods)[0], route.path)
        for route in ROUTES
        if not (_dependency_names(route) & AUTH_DEPENDENCIES)
    }
    unexpected = sorted(open_routes - set(INTENTIONALLY_PUBLIC))
    assert not unexpected, (
        "These routes resolve no user and are not on the public allowlist:\n"
        + "\n".join(f"  {method} {path}" for method, path in unexpected)
    )


def test_the_allowlist_does_not_outlive_the_routes_it_names():
    """A stale entry would quietly re-authorise a future route at the same path."""
    mounted = {(sorted(route.methods)[0], route.path) for route in ROUTES}
    assert not sorted(set(INTENTIONALLY_PUBLIC) - mounted)
