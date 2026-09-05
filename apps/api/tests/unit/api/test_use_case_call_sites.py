"""Route call sites must match their use case signatures.

A route calling UseCase(...).execute(...) with a missing or misspelled
argument raises TypeError at request time, which the transaction decorator
turns into a 500. update_client_tag omitted the required tenant_id, so
every tag update failed and the tenant-isolation check inside the use case
never ran. Static binding catches this without exercising every route.
"""

import ast
import importlib
import inspect
import pkgutil
from pathlib import Path

import pytest

import app.application.use_cases as use_cases_pkg

ROUTES_DIR = Path(__file__).resolve().parents[3] / "app" / "api" / "routes"


def _use_case_signatures() -> dict[str, inspect.Signature]:
    signatures = {}
    for module_info in pkgutil.iter_modules(use_cases_pkg.__path__):
        module = importlib.import_module(f"app.application.use_cases.{module_info.name}")
        for name, obj in vars(module).items():
            if inspect.isclass(obj) and name.endswith("UseCase") and hasattr(obj, "execute"):
                try:
                    signatures[name] = inspect.signature(obj.execute)
                except (TypeError, ValueError):
                    continue
    return signatures


def _execute_call_sites(path: Path):
    """Yield (lineno, use_case_name, positional_count, keyword_names) per call."""
    for node in ast.walk(ast.parse(path.read_text())):
        if not isinstance(node, ast.Call):
            continue
        func = node.func
        if not (isinstance(func, ast.Attribute) and func.attr == "execute"):
            continue
        inner = func.value
        if not (isinstance(inner, ast.Call) and isinstance(inner.func, ast.Name)):
            continue
        keywords = [kw.arg for kw in node.keywords]
        if any(kw is None for kw in keywords):
            continue  # **kwargs spread; cannot bind statically
        yield node.lineno, inner.func.id, len(node.args), keywords


ROUTE_FILES = sorted(ROUTES_DIR.glob("*.py"))


def test_route_files_are_discovered():
    assert len(ROUTE_FILES) > 10


@pytest.mark.parametrize("route_file", ROUTE_FILES, ids=lambda p: p.name)
def test_execute_calls_bind_to_their_use_case(route_file: Path):
    signatures = _use_case_signatures()
    failures = []
    for lineno, use_case, positional, keywords in _execute_call_sites(route_file):
        signature = signatures.get(use_case)
        if signature is None:
            continue
        try:
            signature.bind(None, *[None] * positional, **dict.fromkeys(keywords))
        except TypeError as exc:
            failures.append(f"{route_file.name}:{lineno} {use_case}.execute -> {exc}")
    assert not failures, "\n".join(failures)
