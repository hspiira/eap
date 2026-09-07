"""Extract the client list and their aliases from the reference workbook.

The workbook's Companies sheet is a hand-maintained mapping from every spelling
seen in the activity log (`OG_COMPANY`) to the company it means
(`Company Name`), plus a curated `CANONICAL LIST` column.

Writes `data/taxonomy/clients.json`: one row per client, with the aliases that
resolve to it. The canonical name is never invented; it is taken from the
mapping, and a spelling equal to the canonical name is not repeated as an alias.

    uv run python scripts/extract_companies.py --workbook <path>
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from collections import defaultdict
from pathlib import Path

API_ROOT = Path(__file__).resolve().parent.parent
if str(API_ROOT) not in sys.path:
    sys.path.insert(0, str(API_ROOT))

OUT = API_ROOT / "data" / "taxonomy" / "clients.json"


def _clean(value: object) -> str | None:
    text = str(value).strip() if value is not None else ""
    return text or None


def _normalise(name: str) -> str:
    return re.sub(r"[^a-z0-9]+", " ", name.lower()).strip()


def _code(name: str, used: set[str]) -> str:
    from app.shared.utils.client_csv import generated_client_code

    return generated_client_code(name, used)


def extract(workbook: Path) -> tuple[list[dict], list[str]]:
    import openpyxl

    wb = openpyxl.load_workbook(workbook, read_only=True, data_only=True)
    rows = list(wb["Companies"].iter_rows(values_only=True))[1:]

    aliases: dict[str, set[str]] = defaultdict(set)
    conflicts: dict[str, set[str]] = defaultdict(set)
    notes: list[str] = []

    for row in rows:
        source = _clean(row[0])
        canonical = _clean(row[1]) if len(row) > 1 else None
        if not source:
            continue
        if not canonical:
            notes.append(f"{source!r} has no canonical company and is not imported")
            continue
        conflicts[_normalise(source)].add(canonical)
        if _normalise(source) != _normalise(canonical):
            aliases[canonical].add(source)

    for source, targets in sorted(conflicts.items()):
        if len(targets) > 1:
            notes.append(f"{source!r} maps to several companies {sorted(targets)}; not imported")
            for target in targets:
                aliases.get(target, set()).discard(source)

    curated = {_clean(row[3]) for row in rows if len(row) > 3 and _clean(row[3])}
    mapped = {_clean(row[1]) for row in rows if len(row) > 1 and _clean(row[1])}
    for extra in sorted(mapped - curated):
        notes.append(
            f"{extra!r} is a canonical company in the mapping but absent from the "
            "curated CANONICAL LIST; imported, because the activity log resolves to it"
        )

    used: set[str] = set()
    clients = [
        {
            "name": name,
            "code": _code(name, used),
            "aliases": sorted(aliases.get(name, set())),
        }
        for name in sorted(mapped)
        if name
    ]
    return clients, notes


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--workbook", required=True, type=Path)
    args = parser.parse_args()

    clients, notes = extract(args.workbook)
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(clients, indent=2) + "\n")

    total_aliases = sum(len(c["aliases"]) for c in clients)
    print(f"{OUT.name:16} {len(clients)} clients, {total_aliases} aliases")
    for note in notes:
        print(f"  note: {note}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
