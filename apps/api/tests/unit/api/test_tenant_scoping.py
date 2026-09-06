"""Client-supplied tenant_id must always be validated against the token.

The frontend puts tenant_id on the query string of nearly every request
(see apps/web/src/api/request-shape.ts), so a route that reads it without
require_same_tenant would let any authenticated user address another
tenant's data. app/core/authorization.py states this rule; this test
enforces it.
"""

import ast
from pathlib import Path

import pytest

ROUTES_DIR = Path(__file__).resolve().parents[3] / "app" / "api" / "routes"
ROUTE_FILES = sorted(ROUTES_DIR.glob("*.py"))

# Dependencies that establish tenant scope: either they compare the supplied
# tenant against the token, or they derive it from a loaded entity.
TENANT_GUARDS = (
    "require_same_tenant",
    "_for_current_tenant",
    "require_tenant_role",
)


def _handlers_taking_a_client_tenant(path: Path):
    """Yield (lineno, name, source) for handlers with a tenant_id parameter."""
    source = path.read_text()
    for node in ast.walk(ast.parse(source)):
        if not isinstance(node, ast.AsyncFunctionDef | ast.FunctionDef):
            continue
        segment = ast.get_source_segment(source, node) or ""
        if "tenant_id: str = Query" not in segment:
            continue
        yield node.lineno, node.name, segment


def test_route_files_are_discovered():
    assert len(ROUTE_FILES) > 10


@pytest.mark.parametrize("route_file", ROUTE_FILES, ids=lambda p: p.name)
def test_client_supplied_tenant_is_always_guarded(route_file: Path):
    unguarded = [
        f"{route_file.name}:{lineno} {name} takes tenant_id from the client "
        "but never validates it against the token"
        for lineno, name, segment in _handlers_taking_a_client_tenant(route_file)
        if not any(guard in segment for guard in TENANT_GUARDS)
    ]
    assert not unguarded, "\n".join(unguarded)
