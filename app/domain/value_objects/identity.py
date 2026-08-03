import re
from dataclasses import dataclass


@dataclass(frozen=True)
class TenantCode:
    """
    Represents a unique code for a tenant.

    Attributes:
    - 3-15 characters
    - lowercase
    - alphanumeric with optional hyphen
    - abbreviation-based (not full legal names)
    - immutable once activated
    """

    value: str

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
                + "(e.g., 'acme', 'acme-corp', 'abc123')"
            )


# === Identity Value Objects ===
#
# Each entity has its own ID subclass so the type checker can flag
# cross-type misuse (e.g. passing a PersonId where a UserId is expected).
# Runtime behaviour is identical to the base `Id`: same string validation,
# same equality semantics. Subclasses exist purely for nominal typing.


# === Domain Value Objects ===
@dataclass(frozen=True)
class Email:
    """
    Represents an email address.

    Attributes:
    - <255 characters
    - email address format
    - immutable once activated
    """

    value: str

    def __post_init__(self):
        if not self.value or len(self.value) > 255:
            raise ValueError("Email must be less than 255 characters")
        if not re.match(r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$", self.value):
            raise ValueError("Invalid email address format")
