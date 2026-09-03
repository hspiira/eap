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
    - normalised to lowercase, surrounding whitespace stripped
    - immutable once activated

    Normalisation is the single choke point that keeps provisioning and login
    agreeing on identity. Addresses are case-insensitive in the local part for
    every mail system we care about, but `users.email` is compared with `=` in
    SQL, which is case-SENSITIVE on PostgreSQL. Without normalising here, a user
    provisioned as `Fred.H@corp.com` could never be found by an Azure SSO login,
    which lowercases the UPN claim — they would hit "account has not been
    provisioned" forever, with the two addresses looking identical to a human.

    `#` is permitted in the local part for Azure AD B2B guest UPNs, which take
    the form `fred_gmail.com#EXT#@tenant.onmicrosoft.com`.
    """

    value: str

    def __post_init__(self):
        if not self.value or not self.value.strip():
            raise ValueError("Email must be a non-empty string")
        normalised = self.value.strip().lower()
        if len(normalised) > 255:
            raise ValueError("Email must be less than 255 characters")
        if not re.match(r"^[a-z0-9._%+#-]+@[a-z0-9.-]+\.[a-z]{2,}$", normalised):
            raise ValueError("Invalid email address format")
        # frozen dataclass — bypass the immutability guard to store the
        # normalised form, so every consumer sees one canonical value.
        object.__setattr__(self, "value", normalised)
