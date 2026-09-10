"""
Audit Helper Utilities

Utilities for seamless audit integration with entities and repositories.
"""

from typing import Any

from app.domain.enums import AuditActionType
from app.domain.value_objects.audit import FieldChange


def extract_field_changes(old_entity: Any | None, new_entity: Any) -> list[FieldChange]:
    """What changed between two states of an entity, for `entity_changes`.

    Compares the public dataclass fields. `events` is transient and the two
    timestamps are bookkeeping the audit row already carries, so none of the
    three counts as a change.
    """
    if old_entity is None:
        return [
            FieldChange(
                field_name="id",
                old_value=None,
                new_value=_audit_value(getattr(new_entity, "id", None)),
            )
        ]

    changes = []
    for field in _comparable_fields(new_entity):
        old_value = _audit_value(getattr(old_entity, field, None))
        new_value = _audit_value(getattr(new_entity, field, None))
        if old_value != new_value:
            changes.append(FieldChange(field_name=field, old_value=old_value, new_value=new_value))
    return changes


_SKIP_FIELDS = {"events", "created_at", "updated_at"}

REDACTED = "[redacted]"


def redact_values(field_changes: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Keep which fields moved on a special-category record, drop what they say.

    The audit trail is read by people outside the care team: a diff on a
    session would otherwise copy the note, the presenting issue and the
    diagnosis into `entity_changes` for all of them. Which field a person
    touched, and when, is the auditable fact.
    """
    return [
        {
            **change,
            "old_value": REDACTED if change.get("old_value") is not None else None,
            "new_value": REDACTED if change.get("new_value") is not None else None,
        }
        for change in field_changes
    ]


def _comparable_fields(entity: Any) -> list[str]:
    fields = getattr(entity, "__dataclass_fields__", None)
    names = list(fields) if fields else [k for k in vars(entity) if not k.startswith("_")]
    return [name for name in names if name not in _SKIP_FIELDS]


def _audit_value(value: Any) -> str | None:
    """A field rendered for storage: value objects unwrap, the rest stringify."""
    if value is None:
        return None
    if hasattr(value, "value"):
        value = value.value
    if hasattr(value, "isoformat"):
        return value.isoformat()
    return str(value)


_EXPLICIT_ACTIONS = {
    "DSARErasureExecuted": AuditActionType.DELETE,
    "SessionImportBatchApplied": AuditActionType.IMPORT,
    "MemberImportBatchApplied": AuditActionType.IMPORT,
}
"""Events the substring rules below would file wrongly.

Erasure destroys subject data and reads as an UPDATE to the rules; an applied
import batch writes rows and reads the same way. Both are stated here rather
than by renaming the event, because the name is what a query written against
the existing trail matches on.
"""


def map_domain_event_to_audit_action(event_type: str) -> AuditActionType:
    """
    Map domain event type to audit action type.

    Args:
        event_type: Domain event class name

    Returns:
        AuditActionType
    """
    explicit = _EXPLICIT_ACTIONS.get(event_type)
    if explicit is not None:
        return explicit

    # Extract base action from event name
    event_lower = event_type.lower()

    if "activated" in event_lower or "created" in event_lower:
        return AuditActionType.CREATE
    elif "updated" in event_lower or "modified" in event_lower:
        return AuditActionType.UPDATE
    elif "deleted" in event_lower or "terminated" in event_lower:
        return AuditActionType.DELETE
    elif "verified" in event_lower or "approved" in event_lower:
        return AuditActionType.APPROVE
    elif "rejected" in event_lower or "suspended" in event_lower:
        return AuditActionType.REJECT
    else:
        return AuditActionType.UPDATE


def get_resource_type_from_entity(entity: Any) -> str:
    """
    Get resource type from entity class name.

    Args:
        entity: Domain entity

    Returns:
        Resource type string (e.g., "Tenant", "Person")
    """
    class_name = type(entity).__name__
    # Remove "Entity" suffix if present
    if class_name.endswith("Entity"):
        return class_name[:-6]
    return class_name


def get_resource_id_from_entity(entity: Any) -> str | None:
    """Return the public string id of an entity, or None if absent."""
    if not hasattr(entity, "id"):
        return None
    id_value = entity.id
    if hasattr(id_value, "value"):
        return id_value.value
    return str(id_value)
