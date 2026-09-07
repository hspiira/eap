"""Turn the reference workbook's Staff sheet into a member-import CSV.

The sheet is already close to the roster importer's shape, so this maps the
columns rather than inventing a second import path: the output is fed to
`POST /members/import`, which previews every row and commits each one on its
own.

Two things it resolves and one it refuses. `Company Code` in the sheet is the
client's own shorthand, not the code this system issued, so the company name is
resolved against the environment's clients and aliases and the resolved code is
written out. Gender case is normalised. Identity is never invented: a row whose
Staff_ID carries no number is written to a separate holding file with the
reason, because `employer_member_id` is unique per client and a bare prefix
cannot identify anybody.

    uv run --with openpyxl python scripts/extract_staff.py --workbook <path> \
        --tenant-id <id>
"""

from __future__ import annotations

import argparse
import asyncio
import csv
import io
import os
import re
import sys
from collections import Counter, defaultdict
from pathlib import Path

API_ROOT = Path(__file__).resolve().parent.parent
if str(API_ROOT) not in sys.path:
    sys.path.insert(0, str(API_ROOT))

OUT_DIR = API_ROOT / "data" / "taxonomy"
COLUMNS = [
    "Company Code",
    "Staff_ID",
    "Staff Number",
    "Name of Employee",
    "Email Address",
    "Personal Email",
    "Date of Birth",
    "Gender",
    "Phone",
    "National ID",
    "Passport Number",
    "Status",
    "Relation",
    "Primary Staff ID",
]
GENDERS = {"female": "Female", "male": "Male"}
EMAIL = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s.]+$")


def _clean(value: object) -> str | None:
    text = str(value).strip() if value is not None else ""
    return text or None


def _normalise(name: str) -> str:
    return re.sub(r"[^a-z0-9]+", " ", name.lower()).strip()


async def _client_codes(tenant_id: str) -> dict[str, str]:
    """Every client name and alias in the tenant, mapped to the client's code."""
    from sqlalchemy import text

    from app.core.database import AsyncSessionLocal

    async with AsyncSessionLocal() as session:
        rows = (await session.execute(text("SELECT name, code FROM clients"))).all()
        aliases = (
            await session.execute(
                text(
                    "SELECT ca.alias, c.code FROM client_aliases ca "
                    "JOIN clients c ON c.id = ca.client_id"
                )
            )
        ).all()
    codes = {_normalise(name): code for name, code in rows}
    for alias, code in aliases:
        codes.setdefault(_normalise(alias), code)
    return codes


def _rows(workbook: Path) -> list[dict]:
    import openpyxl

    wb = openpyxl.load_workbook(workbook, read_only=True, data_only=True)
    raw = list(wb["Staff"].iter_rows(values_only=True))
    headers = [_clean(h) or f"col{i}" for i, h in enumerate(raw[0])]
    return [
        dict(zip(headers, row, strict=False))
        for row in raw[1:]
        if any(cell is not None and str(cell).strip() for cell in row)
    ]


def _held(row: int, company: str | None, staff_id: str | None, name: str | None, reason: str):
    return {"row": row, "company": company, "staff_id": staff_id, "name": name, "reason": reason}


def build(rows: list[dict], codes: dict[str, str]) -> tuple[list[dict], list[dict], list[str]]:
    ready: list[dict] = []
    held: list[dict] = []
    notes: list[str] = []
    unresolved: Counter = Counter()
    dropped_emails: list[tuple[str | None, str]] = []
    seen: dict[tuple[str, str], int] = defaultdict(int)

    for index, row in enumerate(rows, start=2):
        company = _clean(row.get("Company"))
        staff_id = _clean(row.get("Staff_ID"))
        number = _clean(row.get("Staff Number"))
        name = _clean(row.get("Name of Employee"))
        code = codes.get(_normalise(company)) if company else None

        if not name:
            held.append(_held(index, company, staff_id, name, "no employee name"))
            continue
        if code is None:
            unresolved[company or "<blank>"] += 1
            held.append(
                _held(
                    index,
                    company,
                    staff_id,
                    name,
                    f"company {company!r} does not resolve to a client by name or alias",
                )
            )
            continue
        if not staff_id or not number:
            # A bare prefix such as "IDI-" is not an identity: every row under
            # it would collide on employer_member_id, and deriving one from the
            # name is exactly the inference the migration rules forbid.
            held.append(_held(index, company, staff_id, name, "Staff_ID carries no staff number"))
            continue

        key = (code, staff_id)
        seen[key] += 1
        if seen[key] > 1:
            held.append(
                _held(
                    index,
                    company,
                    staff_id,
                    name,
                    f"Staff_ID {staff_id!r} repeats within {company!r}",
                )
            )
            continue

        email = _clean(row.get("Email Address")) or ""
        if email and not EMAIL.match(email):
            # Not repaired: a corrected address could reach the wrong person.
            # The employee still belongs on the roster without it.
            dropped_emails.append((staff_id, email))
            email = ""
        gender = _clean(row.get("Gender"))
        ready.append(
            {
                "Company Code": code,
                "Staff_ID": staff_id,
                "Staff Number": number,
                "Name of Employee": name,
                "Email Address": email,
                "Personal Email": "",
                "Date of Birth": "",
                "Gender": GENDERS.get((gender or "").lower(), "") if gender else "",
                "Phone": "",
                "National ID": "",
                "Passport Number": "",
                "Status": _clean(row.get("Status")) or "",
                "Relation": "Employee",
                "Primary Staff ID": "",
            }
        )

    for company, count in unresolved.most_common():
        notes.append(
            f"{company!r}: {count} rows held; add it as an alias of the right client, then re-run"
        )
    if dropped_emails:
        sample = ", ".join(f"{value!r} on {sid}" for sid, value in dropped_emails[:3])
        notes.append(
            f"{len(dropped_emails)} email addresses are not valid and were left blank; "
            f"the person is still imported. Fix them at source: {sample}"
        )
    prefixes = Counter(h["company"] for h in held if h["reason"].endswith("no staff number"))
    for company, count in prefixes.most_common():
        notes.append(
            f"{company!r}: {count} rows have no staff number; the client must supply "
            "Staff_IDs before these people can be on the roster"
        )
    return ready, held, notes


async def run(workbook: Path, tenant_id: str) -> int:
    codes = await _client_codes(tenant_id)
    ready, held, notes = build(_rows(workbook), codes)

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    buffer = io.StringIO(newline="")
    writer = csv.DictWriter(buffer, fieldnames=COLUMNS)
    writer.writeheader()
    writer.writerows(ready)
    (OUT_DIR / "staff_roster.csv").write_text(buffer.getvalue())

    held_buffer = io.StringIO(newline="")
    held_writer = csv.DictWriter(
        held_buffer, fieldnames=["row", "company", "staff_id", "name", "reason"]
    )
    held_writer.writeheader()
    held_writer.writerows(held)
    (OUT_DIR / "staff_roster_held.csv").write_text(held_buffer.getvalue())

    print(f"staff_roster.csv       {len(ready)} rows ready to import")
    print(f"staff_roster_held.csv  {len(held)} rows held for a person")
    for note in notes:
        print(f"  note: {note}")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--workbook", required=True, type=Path)
    parser.add_argument("--tenant-id", required=True)
    args = parser.parse_args()
    os.environ.setdefault("PYTHONWARNINGS", "ignore")
    return asyncio.run(run(args.workbook, args.tenant_id))


if __name__ == "__main__":
    raise SystemExit(main())
