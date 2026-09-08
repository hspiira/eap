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
# ProviderEntity has no silent mutator left. replace_profile, the wholesale
# swap the patch route used to call, is gone; every provider mutation now runs
# through a command that emits. Route-level audit_change is driven by
# entity.events, so a call on an entity that emits nothing is a no-op, which is
# what panel.py did while advertising itself as audit-trailed. That removed two
# from the baseline of 145.
# ProviderAliasEntity.mark_ambiguous and mark_unmapped are the staging
# classifier's output, not decisions: one event per unmatched name would flood
# audit_logs for a file of several thousand rows, and the reviewable state plus
# candidates are persisted on the row. The alias decisions that a person makes,
# resolve and reject, do emit, as do specialty retire/restore and import batch
# apply/abandon.
# SessionImportRowEntity.mark_imported is bookkeeping under an already-audited
# operation: applying a batch emits SessionImportBatchApplied with the actor and
# the accepted count, and one event per imported row would flood audit_logs for
# a file of several thousand. The batch is the auditable act; the rows are its
# detail, and each carries its own imported_session_id.
# PractitionerImportRowEntity.mark_applied and quarantine are the same
# bookkeeping for the practitioner workbook apply: the batch emits
# PractitionerImportBatchApplied with actor and counts, and each row carries
# its created ids and quarantine reason as persisted detail.
# Net of the two the provider work removed, that is 148.
#
# 148 -> 122 in one pass over clients and contracts, which is three separate
# things and worth keeping apart:
#   -14  ClientEntity and ContractEntity now emit on create, on every field
#        update, and on archive and restore. Neither has a silent mutator left.
#    -3  the detector follows a private helper: a method that hands the append
#        to one (ContractEntity._record_status_change) was read as silent.
#    -9  the detector no longer reads `self.x == y` as an assignment, so read
#        predicates like `is_active` were never mutators at all.
# Only the first is coverage. The other twelve were the measurement.
#
# 122 -> 113 extending the same pass outwards: ServiceAssignmentEntity in full,
# and EligibleMember except the three below.
# EligibleMember.link_account and unlink_account stay silent for the reason at
# the top of this list, and record_import is bookkeeping under an import batch
# that already emits: a roster file of three thousand rows would otherwise
# write three thousand audit rows for one operation a person performed once.
# 113 -> 101 with ServiceSessionEntity, which needed the redaction rule first:
# a session carries notes, a presenting issue and a diagnosis, so the handler
# keeps the field names and drops the values for any special-category record.
KNOWN_SILENT_MUTATORS = 101


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


def _emits(cls, source: str, seen: frozenset[str] = frozenset()) -> bool:
    """Whether a method appends an event, itself or through a private helper.

    A method that hands the append to a helper is still audited, and factoring
    a repeated append out is the normal way to write one. Without following the
    call, `ContractEntity.activate` reads as silent while it emits.
    """
    if "events.append" in source:
        return True
    for helper in set(re.findall(r"self\.(_\w+)\(", source)) - seen:
        member = getattr(cls, helper, None)
        if not inspect.isfunction(member):
            continue
        try:
            helper_source = inspect.getsource(member)
        except (OSError, TypeError):
            continue
        if _emits(cls, helper_source, seen | {helper}):
            return True
    return False


def _mutating_methods(cls):
    """Public methods that assign to self, with whether they emit an event."""
    for name, member in vars(cls).items():
        if not inspect.isfunction(member) or name.startswith("_"):
            continue
        try:
            source = inspect.getsource(member)
        except (OSError, TypeError):
            continue
        # `=(?!=)` so a comparison is not read as an assignment: `is_active`
        # returns `self.status == ACTIVE` and mutates nothing.
        if not re.search(r"self\.\w+\s*=(?!=)", source):
            continue
        yield name, _emits(cls, source)


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


def test_creating_a_client_is_audited():
    """Creation emits, and from the use case rather than the constructor.

    A `__post_init__` would fire in the mapper too, which builds an entity for
    every row it reads, so loading a client would record a creation. The
    create use case calls `record_created` instead: see test_client_api.py for
    the outbox row it produces.
    """
    from app.domain.entities.client import ClientEntity

    source = inspect.getsource(ClientEntity)
    assert "__post_init__" not in source, (
        "ClientEntity gained a __post_init__. Emitting there records a "
        "creation every time the mapper hydrates a row."
    )
    assert "ClientCreated" in inspect.getsource(ClientEntity.record_created)


def test_the_commercial_aggregates_are_audited_in_full():
    """The records a dispute is argued from leave no silent mutator behind."""
    gap = silent_mutators()
    for entity in ("ClientEntity", "ContractEntity", "ServiceAssignmentEntity"):
        assert gap.get(entity) is None, f"{entity}: {gap.get(entity)}"


def test_sessions_are_audited_now_that_their_values_are_redacted():
    """Delivery records emit, and the trail names fields rather than content."""
    from app.shared.utils.clinical_data_classification import is_special_category

    gap = silent_mutators()
    assert gap.get("ServiceSessionEntity") is None, gap.get("ServiceSessionEntity")
    assert is_special_category(resource_type="ServiceSession")


def test_only_the_documented_member_mutators_stay_silent():
    """Roster changes emit, apart from the two the route audits itself.

    Account linkage is an association between two aggregates and the members
    route records it as its own operation; record_import is bookkeeping under
    a batch that already emits.
    """
    gap = silent_mutators()
    assert gap.get("EligibleMember") == ["link_account", "record_import", "unlink_account"]
