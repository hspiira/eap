"""
Audit Value Objects

Value objects for audit tracking.
"""

from dataclasses import dataclass


@dataclass(frozen=True)
class FieldChange:
    """
    Represents a single field change in an entity.
    
    Immutable value object capturing before/after values.
    """
    field_name: str
    old_value: str | None
    new_value: str | None
    
    def __post_init__(self) -> None:
        """Validate field change."""
        if not self.field_name:
            raise ValueError("Field name cannot be empty")
