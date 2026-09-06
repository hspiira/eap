"""How much of the domain's state change reaches the audit trail.

Auditing is event-driven: `audit_change` reads `entity.events`, so a
mutating method that appends nothing is invisible to `audit_logs`, no
matter that the outbox and worker are healthy. Most mutating methods emit
nothing today, so the audit trail records lifecycle transitions and little
else. Creating a client, renaming one, or changing its contact details all
leave no record.

This test does not assert that every method must emit; that is a product
decision about audit scope, and for special-category health data it is a
decision worth making deliberately. It pins the current number so the gap
is visible and cannot widen unnoticed.
"""

import importlib
import inspect
import pkgutil
import re

import app.domain.entities as entities_pkg

# Methods that assign to self but emit no domain event, per entity. Lower is
# better. Raise this only with a reason; lower it freely.
# Account linkage is audited by the Members route as an explicit operation
# because it is an association between two aggregates, rather than a member
# lifecycle event. Keep those two domain setters visible in this baseline.
KNOWN_SILENT_MUTATORS = 144


def _entity_classes():
    """Every domain entity dataclass.

    Not filtered on an "Entity" suffix: most aggregates do not use one
    (Case, Authorization, EligibleMember), and filtering on it hides two
    thirds of the domain.
    """
    for module_info in pkgutil.iter_modules(entities_pkg.__path__):
        module = importlib.import_module(f"app.domain.entities.{module_info.name}")
        for name, obj in vars(module).items():
            if not inspect.isclass(obj) or obj.__module__ != module.__name__:
                continue
            if not hasattr(obj, "__dataclass_fields__"):
                continue
            yield name, obj


def _mutating_methods(cls):
    """Public methods that assign to self, with whether they emit an event."""
    for name, member in vars(cls).items():
        if not inspect.isfunction(member) or name.startswith("_"):
            continue
        try:
            source = inspect.getsource(member)
        except (OSError, TypeError):
            continue
        if not re.search(r"self\.\w+\s*=", source):
            continue
        yield name, "events.append" in source


def silent_mutators() -> dict[str, list[str]]:
    """Entity -> mutating methods that leave no audit trail."""
    out: dict[str, list[str]] = {}
    for name, cls in _entity_classes():
        silent = sorted(m for m, emits in _mutating_methods(cls) if not emits)
        if silent:
            out[name] = silent
    return out


def test_the_audit_gap_does_not_widen():
    gap = silent_mutators()
    total = sum(len(v) for v in gap.values())
    detail = "\n".join(f"  {k}: {', '.join(v)}" for k, v in sorted(gap.items()))
    assert total <= KNOWN_SILENT_MUTATORS, (
        f"{total} mutating methods emit no domain event, up from "
        f"{KNOWN_SILENT_MUTATORS}. Each one is a state change that never "
        f"reaches audit_logs:\n{detail}"
    )


def test_lifecycle_transitions_are_audited():
    """The transitions that do emit are the audit trail's actual coverage."""
    emitting = {
        name: sorted(m for m, emits in _mutating_methods(cls) if emits)
        for name, cls in _entity_classes()
    }
    assert "suspend" in emitting.get("ClientEntity", [])
    assert "terminate" in emitting.get("ClientEntity", [])
    assert "activate" in emitting.get("ClientEntity", [])


def test_creating_a_client_is_not_audited():
    """Documents the gap rather than asserting it is acceptable.

    ClientEntity has no __post_init__ emitting a creation event, so
    POST /clients produces no outbox row. Verified against a running API.
    """
    from app.domain.entities.client import ClientEntity

    source = inspect.getsource(ClientEntity)
    assert "__post_init__" not in source, (
        "ClientEntity gained a __post_init__. If it now emits a creation "
        "event, client creation is audited and this test should assert that "
        "instead."
    )
