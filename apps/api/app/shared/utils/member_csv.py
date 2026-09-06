"""Strict CSV parsing for client member rosters."""

from __future__ import annotations

import csv
import io
import re
from dataclasses import dataclass


def _key(value: str) -> str:
    return re.sub(r"[^a-z0-9]+", "_", value.strip().lower()).strip("_")


def _value(row: dict[str, str | None], *keys: str) -> str | None:
    for key in keys:
        value = (row.get(key) or "").strip()
        if value and value.casefold() not in {"n/a", "na", "null", "-"}:
            return value
    return None


@dataclass(frozen=True)
class MemberCsvRow:
    row_number: int
    client_code: str | None
    employer_member_id: str | None
    display_label: str | None
    work_email: str | None
    gender: str | None
    status: str | None
    relation: str | None
    primary_employee_member_id: str | None


def parse_member_csv(content: bytes) -> tuple[list[MemberCsvRow], list[dict[str, object]]]:
    try:
        decoded = content.decode("utf-8-sig")
    except UnicodeDecodeError as exc:
        raise ValueError("CSV must be UTF-8 encoded") from exc
    reader = csv.DictReader(io.StringIO(decoded))
    if not reader.fieldnames:
        raise ValueError("CSV must have a header row")
    headers = {_key(header): header for header in reader.fieldnames if header}
    required = {"staff_id", "name_of_employee"}
    missing = sorted(required - headers.keys())
    if missing:
        raise ValueError(f"CSV must include: {', '.join(missing)}")
    rows: list[MemberCsvRow] = []
    issues: list[dict[str, object]] = []
    for row_number, raw in enumerate(reader, start=2):
        row = {_key(key): value for key, value in raw.items() if key}
        if not any((value or "").strip() for value in raw.values() if value is not None):
            continue
        parsed = MemberCsvRow(
            row_number=row_number,
            client_code=_value(row, "company_code", "client_code"),
            # Staff Number is deliberately not an identity fallback.  It is often
            # payroll-scoped and may be blank/reused; only an explicit Staff_ID or
            # employer_member_id is safe for idempotent roster imports.
            employer_member_id=_value(row, "staff_id", "employer_member_id"),
            display_label=_value(row, "name_of_employee", "display_label", "name"),
            work_email=_value(row, "email_address", "work_email", "email"),
            gender=_value(row, "gender"),
            status=_value(row, "status"),
            relation=_value(row, "relation", "member_relation"),
            primary_employee_member_id=_value(
                row, "primary_staff_id", "primary_employee_member_id"
            ),
        )
        rows.append(parsed)
        if not parsed.client_code:
            issues.append({"row": row_number, "field": "Company Code", "message": "Client code is required"})
        if not parsed.employer_member_id or parsed.employer_member_id.endswith("-"):
            issues.append({"row": row_number, "field": "Staff_ID", "message": "Stable Staff_ID is required"})
        if not parsed.display_label:
            issues.append({"row": row_number, "field": "Name of Employee", "message": "Member name is required"})
    return rows, issues
