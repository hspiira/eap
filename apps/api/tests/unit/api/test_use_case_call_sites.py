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

#: The dispatcher is also driven from the application layer (tenant bootstrap
#: activates its own admin user), so the tenant guard has to be scanned there.
USE_CASES_DIR = Path(__file__).resolve().parents[3] / "app" / "application" / "use_cases"
TRANSITION_CALLER_FILES = ROUTE_FILES + sorted(USE_CASES_DIR.glob("*.py"))


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


def _entity_classes() -> dict[str, type]:
    import app.domain.entities as entities_pkg

    classes = {}
    for module_info in pkgutil.iter_modules(entities_pkg.__path__):
        module = importlib.import_module(f"app.domain.entities.{module_info.name}")
        for name, obj in vars(module).items():
            if inspect.isclass(obj) and name.endswith("Entity"):
                classes[name] = obj
    return classes


def _transition_call_sites(path: Path):
    """Yield (lineno, enum_name, member_name, keyword_names) per transition call."""
    for node in ast.walk(ast.parse(path.read_text())):
        if not isinstance(node, ast.Call):
            continue
        func = node.func
        if not (isinstance(func, ast.Attribute) and func.attr == "execute"):
            continue
        if len(node.args) < 2:
            continue
        second = node.args[1]
        if not (isinstance(second, ast.Attribute) and isinstance(second.value, ast.Name)):
            continue
        if not second.value.id.endswith("Transition"):
            continue
        keywords = [kw.arg for kw in node.keywords]
        if any(kw is None for kw in keywords):
            continue
        # `tenant_id` is the dispatcher's own ownership argument; it is consumed
        # by TransitionUseCase.execute and never forwarded to the entity method.
        yield node.lineno, second.value.id, second.attr, [k for k in keywords if k != "tenant_id"]


@pytest.mark.parametrize("route_file", ROUTE_FILES, ids=lambda p: p.name)
def test_transition_calls_bind_to_their_entity_method(route_file: Path):
    """TransitionUseCase forwards **kwargs straight to the entity method.

    A route passing a keyword the entity does not accept raises TypeError at
    request time. POST /services/{id}/deactivate?reason=... did exactly that.
    """
    from app.application.use_cases import transitions

    entities = _entity_classes()
    failures = []
    for lineno, enum_name, member_name, keywords in _transition_call_sites(route_file):
        enum_cls = getattr(transitions, enum_name, None)
        member = getattr(enum_cls, member_name, None) if enum_cls else None
        if member is None:
            continue
        entity = entities.get(f"{enum_name.replace('Transition', '')}Entity")
        if entity is None:
            continue
        method = getattr(entity, member.value, None)
        if method is None:
            failures.append(f"{route_file.name}:{lineno} {entity.__name__} has no '{member.value}'")
            continue
        try:
            inspect.signature(method).bind(None, **dict.fromkeys(keywords))
        except TypeError as exc:
            failures.append(
                f"{route_file.name}:{lineno} {entity.__name__}.{member.value}"
                f"({', '.join(keywords)}) -> {exc}"
            )
    assert not failures, "\n".join(failures)


# --- Authorization guards must actually run -----------------------------------
#
# SEC-02: twelve routes called the async `require_same_tenant` directly in the
# route body. Python builds the coroutine, nobody awaits it, and the tenant
# check never runs; the arguments were reversed too, so `await` alone would not
# have fixed it. A tenant-A Viewer received tenant-B engagements and surveys
# with 200. The synchronous `assert_same_tenant` is the in-body guard now, and
# these tests fail the build if the async form comes back outside `Depends`.

ASYNC_AUTH_HELPERS = {"require_same_tenant"}


def _bare_calls(path: Path, names: set[str]):
    """Yield (lineno, name) for calls to `names` that are not inside Depends(...)."""
    tree = ast.parse(path.read_text())
    inside_depends = set()
    for node in ast.walk(tree):
        if (
            isinstance(node, ast.Call)
            and isinstance(node.func, ast.Name)
            and node.func.id == "Depends"
        ):
            for arg in ast.walk(node):
                inside_depends.add(id(arg))
    for node in ast.walk(tree):
        if not (isinstance(node, ast.Call) and isinstance(node.func, ast.Name)):
            continue
        if node.func.id in names and id(node) not in inside_depends:
            yield node.lineno, node.func.id


@pytest.mark.parametrize("route_file", ROUTE_FILES, ids=lambda p: p.name)
def test_async_authorization_helpers_are_only_used_as_dependencies(route_file: Path):
    offenders = [
        f"{route_file.name}:{lineno} {name}() is a coroutine; it is only enforced as "
        f"Depends({name}). Use assert_same_tenant(current_user, tenant_id) in a route body."
        for lineno, name in _bare_calls(route_file, ASYNC_AUTH_HELPERS)
    ]
    assert not offenders, "\n".join(offenders)


def test_the_in_body_tenant_guard_stays_synchronous():
    """`assert_same_tenant` exists to be impossible to forget to await."""
    from app.core.authorization import assert_same_tenant

    assert not inspect.iscoroutinefunction(assert_same_tenant)


# --- Every transition must name the tenant it is allowed to touch --------------


def _transition_execute_calls(path: Path):
    """Yield (lineno, function_name, keyword_names) per TransitionUseCase call.

    Resolved inside one function body: routes reuse the name `use_case` for
    different classes, so a file-wide map attributes calls to the wrong class.
    """
    tree = ast.parse(path.read_text())
    for fn in ast.walk(tree):
        if not isinstance(fn, (ast.FunctionDef, ast.AsyncFunctionDef)):
            continue
        names = {
            node.targets[0].id
            for node in ast.walk(fn)
            if isinstance(node, ast.Assign)
            and len(node.targets) == 1
            and isinstance(node.targets[0], ast.Name)
            and isinstance(node.value, ast.Call)
            and isinstance(node.value.func, ast.Name)
            and node.value.func.id == "TransitionUseCase"
        }
        if not names:
            continue
        for node in ast.walk(fn):
            if not isinstance(node, ast.Call):
                continue
            func = node.func
            if not (isinstance(func, ast.Attribute) and func.attr == "execute"):
                continue
            if not (isinstance(func.value, ast.Name) and func.value.id in names):
                continue
            yield node.lineno, fn.name, [kw.arg for kw in node.keywords]


@pytest.mark.parametrize("route_file", TRANSITION_CALLER_FILES, ids=lambda p: p.name)
def test_every_transition_passes_the_tenant_it_may_act_on(route_file: Path):
    """SEC-03: the dispatcher loaded by id and mutated without an owner check.

    A tenant-A Viewer activated tenant-B's survey and added a deliverable to
    tenant-B's engagement. `tenant_id` is keyword-only and has no default, so
    Python already rejects a call that omits it; this test names the offender
    at its line instead of at the first request that reaches it.
    """
    missing = [
        f"{route_file.name}:{lineno} {name}() calls TransitionUseCase.execute without tenant_id"
        for lineno, name, keywords in _transition_execute_calls(route_file)
        if "tenant_id" not in keywords
    ]
    assert not missing, "\n".join(missing)
