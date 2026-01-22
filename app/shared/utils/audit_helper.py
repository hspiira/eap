"""
Audit Helper Utilities

Utilities for seamless audit integration with entities and repositories.
"""

from typing import Any

from app.domain.enums import AuditActionType
from app.domain.value_objects.audit import FieldChange


def extract_field_changes(
    old_entity: Any | None, new_entity: Any
) -> list[FieldChange]:
    """
    Extract field changes between old and new entity states.
    
    Args:
        old_entity: Previous entity state (None for creates)
        new_entity: Current entity state
        
    Returns:
        List of FieldChange value objects
    """
    changes = []

    if old_entity is None:
        # For creates, we don't track all fields (too verbose)
        # Only track key identifying fields
        if hasattr(new_entity, "_id"):
            changes.append(
                FieldChange(
                    field_name="id",
                    old_value=None,
                    new_value=new_entity._id.value if hasattr(new_entity._id, "value") else str(new_entity._id),
                )
            )
        return changes

    # Compare fields (only private fields starting with _)
    old_dict = {
        k: v
        for k, v in old_entity.__dict__.items()
        if k.startswith("_") and not k.startswith("__")
    }
    new_dict = {
        k: v
        for k, v in new_entity.__dict__.items()
        if k.startswith("_") and not k.startswith("__")
    }

    # Skip events and deleted_at for change tracking
    skip_fields = {"_events", "_deleted_at"}

    # Find changed fields
    all_fields = set(old_dict.keys()) | set(new_dict.keys())
    for field in all_fields:
        if field in skip_fields:
            continue

        old_value = old_dict.get(field)
        new_value = new_dict.get(field)

        # Convert value objects to strings
        if hasattr(old_value, "value"):
            old_value = old_value.value
        if hasattr(new_value, "value"):
            new_value = new_value.value

        # Convert to strings for comparison
        old_str = str(old_value) if old_value is not None else None
        new_str = str(new_value) if new_value is not None else None

        # Only track if changed
        if old_str != new_str:
            changes.append(
                FieldChange(
                    field_name=field.lstrip("_"),  # Remove leading underscore
                    old_value=old_str,
                    new_value=new_str,
                )
            )

    return changes


def map_domain_event_to_audit_action(event_type: str) -> AuditActionType:
    """
    Map domain event type to audit action type.
    
    Args:
        event_type: Domain event class name
        
    Returns:
        AuditActionType
    """
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
    """
    Get resource ID from entity.
    
    Args:
        entity: Domain entity
        
    Returns:
        Resource ID string or None
    """
    if hasattr(entity, "_id"):
        id_value = entity._id
        if hasattr(id_value, "value"):
            return id_value.value
        return str(id_value)
    return None
