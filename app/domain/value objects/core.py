"""
Domain value objects for the core domain.

Value objects are immutable types that represent domain concepts with self-validation.
They have no identity, only value.
"""

from datetime import datetime
import re
from typing import Optional
from pydantic import BaseModel, Field, EmailStr

class TenantCode:
    """
    Tenant code value object

    Represents a unique code for a tenant.

    Attributes:
    - 3-15 characters
    - lowercase
    - alphanumeric with optional hyphen
    - abbreviation-based (not full legal names)
    - immutable once activated
    """
    code: str

    def __post_init__(self):
        if not self.value:
            raise ValueError("Tenant code must be a non-empty string")

        # Length validation
        if len(self.value) < 3 or len(self.value) > 15:
            raise ValueError("Tenant code must be 3-15 characters")

        # Format validation: lowercase alphanumeric with optional hyphens
        if not re.match(r"^[a-z0-9]+(-[a-z0-9]+)*$", self.value):
            raise ValueError(
                "Tenant code must be lowercase alphanumeric with optional hyphens "
                "(e.g., 'acme', 'acme-corp', 'abc123')"
            )