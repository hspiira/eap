"""CSV parsing and formatting helpers for client import/export."""

from __future__ import annotations

import csv
import io
import re
from dataclasses import dataclass
from typing import TypedDict

CLIENT_IMPORT_HEADERS = [
    "name",
    "code",
    "phone",
    "email",
    "address",
    "billing_street",
    "billing_city",
    "billing_country",
    "billing_postal_code",
    "industry",
    "parent_client_name",
    "preferred_contact_method",
    "aliases",
]

CLIENT_EXPORT_HEADERS = [
    "id",
    *CLIENT_IMPORT_HEADERS,
    "industry_id",
    "parent_client_id",
    "status",
    "tier",
    "is_verified",
]


@dataclass(frozen=True)
class ClientCsvRow:
    """Normalized values read from one CSV row."""

    row_number: int
    name: str
    code: str | None
    phone: str | None
    email: str | None
    address: str | None
    billing_street: str | None
    billing_city: str | None
    billing_country: str | None
    billing_postal_code: str | None
    industry: str | None
    industry_id: str | None
    parent_client_name: str | None
    parent_client_id: str | None
    preferred_contact_method: str | None
    aliases: tuple[str, ...] = ()


class Issue(TypedDict):
    """One problem found in an imported CSV row."""

    row: int
    field: str | None
    message: str
    severity: str


def _header_key(value: str) -> str:
    return re.sub(r"[^a-z0-9]+", "_", value.strip().lower()).strip("_")


def _clean(value: str | None) -> str | None:
    value = value.strip() if value is not None else ""
    return value or None


def _value(row: dict[str, str | None], *keys: str) -> str | None:
    for key in keys:
        value = _clean(row.get(key))
        if value is not None:
            return value
    return None


def parse_client_csv(content: bytes) -> tuple[list[ClientCsvRow], list[Issue]]:
    """Parse supported client CSV columns, including the supplied sample's names."""
    try:
        text = content.decode("utf-8-sig")
    except UnicodeDecodeError as exc:
        raise ValueError("CSV must be UTF-8 encoded") from exc

    reader = csv.DictReader(io.StringIO(text))
    if not reader.fieldnames:
        raise ValueError("CSV must have a header row")

    normalized_headers = {_header_key(header): header for header in reader.fieldnames if header}
    name_headers = (
        "name",
        "client_name",
        "company_name",
        "canonical_name",
        "company",
        "canonical_list",
        "og_company",
    )
    if not any(header in normalized_headers for header in name_headers):
        raise ValueError("CSV must include a name column (name, Company Name, or canonical list)")

    rows: list[ClientCsvRow] = []
    issues: list[Issue] = []
    for row_number, raw_row in enumerate(reader, start=2):
        row = {_header_key(key): value for key, value in raw_row.items() if key is not None}
        if not any(_clean(value) for value in raw_row.values() if value is not None):
            continue

        name = _value(
            row,
            "name",
            "client_name",
            "company_name",
            "canonical_name",
            "company",
            "canonical_list",
            "og_company",
        )
        if not name:
            issues.append(
                {"row": row_number, "field": "name", "message": "Name is required", "severity": "error"}
            )
            continue

        billing_values = {
            field: _value(row, field)
            for field in (
                "billing_street",
                "billing_city",
                "billing_country",
                "billing_postal_code",
            )
        }
        if any(billing_values.values()) and not all(
            billing_values[field] for field in ("billing_street", "billing_city", "billing_country")
        ):
            issues.append(
                {
                    "row": row_number,
                    "field": "billing_address",
                    "message": "billing_street, billing_city, and billing_country are required together",
                    "severity": "error",
                }
            )
            continue

        rows.append(
            ClientCsvRow(
                row_number=row_number,
                name=name,
                code=_value(row, "code", "client_code"),
                phone=_value(row, "phone", "contact_phone"),
                email=_value(row, "email", "contact_email"),
                address=_value(row, "address", "contact_address"),
                billing_street=billing_values["billing_street"],
                billing_city=billing_values["billing_city"],
                billing_country=billing_values["billing_country"],
                billing_postal_code=billing_values["billing_postal_code"],
                industry=_value(row, "industry", "industry_name"),
                industry_id=_value(row, "industry_id"),
                parent_client_name=_value(row, "parent_client_name", "parent_client"),
                parent_client_id=_value(row, "parent_client_id", "parent_id"),
                preferred_contact_method=_value(row, "preferred_contact_method", "contact_method"),
                aliases=_parse_aliases(row, name),
            )
        )

    return rows, issues


def _parse_aliases(row: dict[str, str | None], name: str) -> tuple[str, ...]:
    """Read explicit aliases and the supplied sample's OG_COMPANY column."""
    values = []
    for value in (_value(row, "aliases", "alias"), _value(row, "og_company", "original_company")):
        if value:
            values.extend(part.strip() for part in value.split(";") if part.strip())
    return tuple(dict.fromkeys(value for value in values if value.casefold() != name.casefold()))


def generated_client_code(name: str, used_codes: set[str]) -> str:
    """Create a stable, unique 3–5 character code when a CSV omits one."""
    words = re.findall(r"[A-Za-z0-9]+", name.upper())
    initials = "".join(word[0] for word in words)
    compact = "".join(words)
    base = (initials if len(initials) >= 3 else compact)[:5]
    base = (base + "CLI")[:5]

    candidate = base
    suffix = 2
    while candidate in used_codes:
        suffix_text = str(suffix)
        candidate = (base[: 5 - len(suffix_text)] + suffix_text)[:5]
        suffix += 1
    used_codes.add(candidate)
    return candidate
