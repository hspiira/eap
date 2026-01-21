"""
Domain value objects for the Allevia core domain.

Value objects are immutable types that represent domain concepts with self-validation.
They have no identity, only value.
"""

from ast import Tuple
from dataclasses import dataclass
from datetime import date, datetime
from pyexpat import features
import re
from typing import Optional
from pydantic import BaseModel, Field, EmailStr


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
                "(e.g., 'acme', 'acme-corp', 'abc123')"
            )

# === Identity Value Objects ===

@dataclass(frozen=True)
class Id:
    """
    Represents a unique identifier for an entity.

    Attributes:
    - <25 characters
    - alphanumeric with optional hyphen
    - immutable once activated
    """
    value: str
    def __post_init__(self):
        if not self.value or len(self.value) > 25:
            raise ValueError("ID must be less than 25 characters")

TenantId = Id # Alias for Id
PersonId = Id # Alias for Id
ContractId = Id # Alias for Id
ServiceId = Id # Alias for Id


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
            raise ValueError(f"{self.value} is not a valid email address")

@dataclass(frozen=True)
class Money:
    amount: float
    currency: str
    def __post_init__(self):
        if not self.amount or self.amount < 0:
            raise ValueError("Amount must be a positive number")
        if not self.currency or len(self.currency) != 3:
            raise ValueError("Currency must be a 3-letter ISO code")
    def add(self, other: 'Money') -> 'Money':
        if self.currency != other.currency:
            raise ValueError("Currencies must be the same")
        return Money(self.amount + other.amount, self.currency)
    def subtract(self, other: 'Money') -> 'Money':
        if self.currency != other.currency:
            raise ValueError("Currencies must be the same")
        return Money(self.amount - other.amount, self.currency)
    def multiply(self, other: 'Money') -> 'Money':
        return Money(self.amount * other.amount, self.currency)
    def divide(self, other: 'Money') -> 'Money':
        return Money(self.amount / other.amount, self.currency)

@dataclass(frozen=True)
class DateRange:
    start_date: datetime
    end_date: datetime
    def __post_init__(self):
        if self.start_date > self.end_date:
            raise ValueError("Start date must be before end date")
    @property
    def days(self) -> int:
        return (self.end_date - self.start_date).days
    @property
    def months(self) -> int:
        return (self.end_date.year - self.start_date.year) * 12 + (self.end_date.month - self.start_date.month)
    @property
    def years(self) -> int:
        return self.end_date.year - self.start_date.year
    def contains(self, date: datetime) -> bool:
        return self.start_date <= date <= self.end_date
    def extend_to(self, new_end: date) -> 'DateRange':
        return DateRange(self.start_date, new_end)

@dataclass(frozen=True)
class TenantSettings:
    max_users: int
    max_clients: int
    features_enabled: Tuple[str, ...]
    custom_branding: bool=False
    def allows_more_users(self, current_count: int) -> bool:
        return current_count < self.max_users
