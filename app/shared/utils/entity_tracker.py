"""
Entity Tracker

Utility for tracking entity state changes for audit purposes.
"""

from typing import Any


class EntityTracker:
    """
    Tracks entity state before and after operations.

    Usage:
        tracker = EntityTracker()
        old_entity = await repo.get_by_id(id)
        # ... perform operation ...
        new_entity = await repo.get_by_id(id)
        changes = tracker.get_changes(old_entity, new_entity)
    """

    @staticmethod
    def get_entity_snapshot(entity: Any) -> dict[str, Any]:
        """
        Create a snapshot of entity state.

        Args:
            entity: Domain entity

        Returns:
            Dictionary snapshot of entity state
        """
        if entity is None:
            return {}

        snapshot = {}
        for key, value in entity.__dict__.items():
            if key.startswith("_") and not key.startswith("__"):
                # Skip events and internal tracking
                if key not in {"_events", "_deleted_at"}:
                    # Convert value objects to their values
                    if hasattr(value, "value"):
                        snapshot[key] = value.value
                    else:
                        snapshot[key] = value

        return snapshot

    @staticmethod
    def compare_snapshots(
        old_snapshot: dict[str, Any], new_snapshot: dict[str, Any]
    ) -> dict[str, tuple[Any, Any]]:
        """
        Compare two entity snapshots and return changes.

        Args:
            old_snapshot: Previous entity snapshot
            new_snapshot: Current entity snapshot

        Returns:
            Dictionary mapping field names to (old_value, new_value) tuples
        """
        changes = {}

        # Check all fields in both snapshots
        all_fields = set(old_snapshot.keys()) | set(new_snapshot.keys())

        for field in all_fields:
            old_value = old_snapshot.get(field)
            new_value = new_snapshot.get(field)

            # Only track if changed
            if old_value != new_value:
                changes[field] = (old_value, new_value)

        return changes
