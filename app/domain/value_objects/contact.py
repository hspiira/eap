from dataclasses import dataclass

from app.domain.value_objects.identity import Email


@dataclass(frozen=True)
class ContactInfo:
    phone: str | None = None
    email: Email | None = None
    address: str | None = None

    def has_any_contact(self) -> bool:
        return bool(self.phone or self.email or self.address)


@dataclass(frozen=True)
class Address:
    street: str
    city: str
    country: str
    postal_code: str | None = None

    def __post_init__(self):
        if not self.street or not self.city or not self.country:
            raise ValueError("Address requires street, city, country")


@dataclass(frozen=True)
class EmergencyContact:
    name: str
    phone: str | None = None
    email: Email | None = None

    def __post_init__(self):
        if not self.name:
            raise ValueError("Emergency contact name required")
        # Validate that at least one of phone or email is non-empty
        # (not None and not empty string)
        phone_provided = bool(self.phone and self.phone.strip())
        email_provided = self.email is not None
        if not phone_provided and not email_provided:
            raise ValueError("Emergency contact needs phone or email")
