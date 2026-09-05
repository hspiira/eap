"""Every diagnosis write is gated, and the two gates are not interchangeable.

The taxonomy is global, so a tenant admin writing to it would give twenty
tenants twenty spellings of the same concept and break cross-tenant prevalence.
Tenant preference goes to the overlay instead. See SERVICES_MIGRATION.md.
"""

from fastapi.routing import APIRoute

from app.api.routes.diagnoses import router
from app.core.authorization import require_platform_admin
from app.domain.enums import TenantRole

WRITE_METHODS = {"POST", "PATCH", "PUT", "DELETE"}


def _dependency_callables(route: APIRoute) -> set:
    return {d.call for d in route.dependant.dependencies}


def _routes():
    return [r for r in router.routes if isinstance(r, APIRoute)]


def _write_routes():
    return [r for r in _routes() if r.methods & WRITE_METHODS]


def test_there_are_write_routes_to_check():
    assert len(_write_routes()) == 7


def test_no_write_route_is_ungated():
    for route in _write_routes():
        assert _dependency_callables(route), f"{route.path} has no dependency gate"


def test_taxonomy_writes_require_platform_admin():
    taxonomy = [r for r in _write_routes() if not r.path.endswith("/settings")]
    assert taxonomy
    for route in taxonomy:
        assert require_platform_admin in _dependency_callables(route), route.path


def _closure_values(fn):
    return [c.cell_contents for c in (fn.__closure__ or ())]


def _overlay_roles():
    overlay = next(r for r in _write_routes() if r.path.endswith("/settings"))
    return [
        v
        for d in _dependency_callables(overlay)
        for v in _closure_values(d)
        if isinstance(v, tuple)
    ]


def test_overlay_write_is_tenant_admin_not_platform():
    overlay = next(r for r in _write_routes() if r.path.endswith("/settings"))
    assert require_platform_admin not in _dependency_callables(overlay)
    assert (TenantRole.ADMIN,) in _overlay_roles(), "overlay write is not gated on tenant ADMIN"


def test_overlay_gate_excludes_viewer_and_user():
    roles = _overlay_roles()[0]
    assert TenantRole.VIEWER not in roles
    assert TenantRole.USER not in roles


def test_reads_are_not_platform_gated():
    reads = [r for r in _routes() if not (r.methods & WRITE_METHODS)]
    for route in reads:
        assert require_platform_admin not in _dependency_callables(route), route.path
