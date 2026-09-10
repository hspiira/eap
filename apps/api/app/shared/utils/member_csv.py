"""Strict CSV parsing for client member rosters."""

from __future__ import annotations

import csv
import io
import re
from dataclasses import dataclass
from datetime import date


def _key(value: str) -> str:
    return re.sub(r"[^a-z0-9]+", "_", value.strip().lower()).strip("_")


def _value(row: dict[str, str | None], *keys: str) -> str | None:
    for key in keys:
        value = (row.get(key) or "").strip()
        if value and value.casefold() not in {"n/a", "#n/a", "na", "null", "-"}:
            return value
    return None


_DATE_PARTS = re.compile(r"[/-]")


def parse_roster_date(value: str) -> date:
    """A calendar date from free-form roster text.

    Tries ISO (`YYYY-MM-DD`) first, since it is unambiguous and is what the
    downloadable template uses. Otherwise splits on `/` or `-` and resolves
    day-first: `03/04/2026` reads as 3 April, not March 4, matching the
    region this importer serves. Falls back to month-first only when the
    day-first reading is not a real calendar date (`12/25/2026` cannot be
    day 12 of month 25) -- there is no way to tell a genuinely ambiguous
    date apart from a mistyped one, so day-first always wins when both read.
    """
    text = value.strip()
    try:
        return date.fromisoformat(text)
    except ValueError:
        pass
    parts = [part.strip() for part in _DATE_PARTS.split(text)]
    if len(parts) != 3 or len(parts[2]) != 4:
        raise ValueError(f"Unrecognised date: {value!r}")
    first, second, year = parts
    try:
        return date(int(year), int(second), int(first))
    except ValueError:
        pass
    try:
        return date(int(year), int(first), int(second))
    except ValueError:
        raise ValueError(f"Unrecognised date: {value!r}") from None


def is_employee_relation(relation: str | None) -> bool:
    """Whether a roster row's Relation column names the employee, not a dependant.

    Blank defaults to Employee, matching the default `_member_create` applies
    when writing the row. A dependant is identified by their Primary Staff ID
    instead of their own Staff_ID; only an employee row needs one.
    """
    return not relation or relation.strip().casefold() == "employee"


@dataclass(frozen=True)
class MemberCsvRow:
    row_number: int
    client_code: str | None
    import_source_id: str | None
    staff_number: str | None
    display_label: str | None
    work_email: str | None
    personal_email: str | None
    gender: str | None
    date_of_birth: str | None
    date_joined: str | None
    phone: str | None
    national_id: str | None
    passport_number: str | None
    job_title: str | None
    job_classification: str | None
    skill: str | None
    department: str | None
    unit: str | None
    employment_type: str | None
    status: str | None
    relation: str | None
    primary_import_source_id: str | None


REQUIRED_HEADERS = {"staff_id", "name_of_employee"}


def _reader(content: bytes) -> csv.DictReader[str]:
    """A reader over the decoded file, rejecting anything the mapping cannot use."""
    try:
        decoded = content.decode("utf-8-sig")
    except UnicodeDecodeError as exc:
        raise ValueError("CSV must be UTF-8 encoded") from exc
    reader = csv.DictReader(io.StringIO(decoded))
    if not reader.fieldnames:
        raise ValueError("CSV must have a header row")
    headers = {_key(header) for header in reader.fieldnames if header}
    missing = sorted(REQUIRED_HEADERS - headers)
    if missing:
        raise ValueError(f"CSV must include: {', '.join(missing)}")
    return reader


def _parse_row(row_number: int, row: dict[str, str | None]) -> MemberCsvRow:
    return MemberCsvRow(
        row_number=row_number,
        client_code=_value(row, "company_code", "client_code"),
        # Staff Number is deliberately not an identity fallback.  It is often
        # payroll-scoped and may be blank/reused; only an explicit Staff_ID or
        # import_source_id is safe for idempotent roster imports. This is the
        # employer's own reference for matching re-imports; the member code
        # itself is always assigned by the server, never taken from the sheet.
        import_source_id=_value(row, "staff_id", "import_source_id"),
        staff_number=_value(row, "staff_number"),
        display_label=_value(row, "name_of_employee", "display_label", "name"),
        work_email=_value(row, "email_address", "work_email", "email"),
        personal_email=_value(row, "personal_email", "personal_email_address"),
        gender=_value(row, "gender"),
        date_of_birth=_value(row, "date_of_birth", "dob"),
        date_joined=_value(row, "date_joined", "member_since", "coverage_start"),
        phone=_value(row, "phone", "phone_number", "mobile"),
        national_id=_value(row, "national_id", "national_identification_number"),
        passport_number=_value(row, "passport_number", "passport"),
        job_title=_value(row, "job_title"),
        job_classification=_value(row, "job_classification", "classification"),
        skill=_value(row, "skill"),
        department=_value(row, "department"),
        unit=_value(row, "unit"),
        employment_type=_value(row, "contract_type", "employment_type"),
        status=_value(row, "status"),
        relation=_value(row, "relation", "member_relation"),
        primary_import_source_id=_value(row, "primary_staff_id", "primary_import_source_id"),
    )


def _row_issues(parsed: MemberCsvRow) -> list[dict[str, object]]:
    """Everything wrong with one row, by the source file's column names."""
    issues: list[dict[str, object]] = []
    if not parsed.client_code:
        issues.append({"field": "Company Code", "message": "Client code is required"})
    # A dependant is identified by Primary Staff ID, not their own; blank is only
    # an error for the employee row. A dirty value (still ending in "-") is
    # wrong data regardless of relation.
    if (parsed.import_source_id and parsed.import_source_id.endswith("-")) or (
        not parsed.import_source_id and is_employee_relation(parsed.relation)
    ):
        issues.append({"field": "Staff_ID", "message": "Stable Staff_ID is required"})
    if not parsed.display_label:
        issues.append({"field": "Name of Employee", "message": "Member name is required"})
    return [{"row": parsed.row_number, **issue} for issue in issues]


def _is_blank(raw: dict[str, str | None]) -> bool:
    return not any((value or "").strip() for value in raw.values() if value is not None)


def parse_member_csv(content: bytes) -> tuple[list[MemberCsvRow], list[dict[str, object]]]:
    rows: list[MemberCsvRow] = []
    issues: list[dict[str, object]] = []
    for row_number, raw in enumerate(_reader(content), start=2):
        if _is_blank(raw):
            continue
        parsed = _parse_row(row_number, {_key(key): value for key, value in raw.items() if key})
        rows.append(parsed)
        issues.extend(_row_issues(parsed))
    return rows, issues
