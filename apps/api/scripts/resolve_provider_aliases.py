"""Resolve source practitioner names to practitioners, from recorded decisions.

Two decisions are honoured here, and nothing else. The first is provenance: a
practitioner import batch records which row created which practitioner, so an
alias staged from that row names that practitioner as a matter of record, not
of resemblance. The second is a reviewed mapping sheet, in which a person wrote
the canonical name for each spelling the source uses.

Decision 5 stands: a normalised name is not identity. An alias whose spelling
merely looks like a practitioner's, with no batch row and no sheet entry behind
it, is left unmapped for a person to decide.

`--source-system` with `--names` queues every name a source file uses before
resolving, because staging reads decisions and never opens one: a source system
whose names nobody has queued has nothing for a reviewer to act on.

    uv run python scripts/resolve_provider_aliases.py --tenant-id <id> \
        --batch-id <id> [--mapping <xlsx> --sheet Counselors] [--apply]

    uv run python scripts/resolve_provider_aliases.py --tenant-id <id> \
        --batch-id <id> --source-system activity-log-workbook \
        --names data/taxonomy/sessions.csv --mapping <xlsx> [--apply]
"""

from __future__ import annotations

import argparse
import asyncio
import os
import sys
from pathlib import Path

SCRIPTS_DIR = Path(__file__).resolve().parent
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

API_ROOT = SCRIPTS_DIR.parent
if str(API_ROOT) not in sys.path:
    sys.path.insert(0, str(API_ROOT))

from import_support import Plan, report, send  # noqa: E402

PAGE = 100
#: Columns a source extract may hold the practitioner's name in, most
#: deliberately cleaned first. Matches what the staging parser looks for.
NAME_COLUMNS = ("COUNSELOR (CLEAN)", "COUNSELOR", "COUNSELLOR")


def _mapping(workbook: Path | None, sheet: str) -> dict[str, str]:
    """Read the reviewed sheet as normalised source name -> canonical name."""
    if workbook is None:
        return {}
    import openpyxl

    from app.domain.services.provider_alias_normalisation import normalise_practitioner_name

    rows = openpyxl.load_workbook(workbook, read_only=True)[sheet].iter_rows(
        min_row=2, values_only=True
    )
    pairs: dict[str, str] = {}
    for source, canonical, *_ in rows:
        if not source or not canonical:
            continue
        key = normalise_practitioner_name(str(source))
        if key:
            pairs[key] = str(canonical).strip()
    return pairs


def _source_names(path: Path | None) -> list[str]:
    """Every distinct practitioner name the extract uses, in first-seen order."""
    if path is None:
        return []
    import csv

    from app.domain.services.provider_alias_normalisation import normalise_practitioner_name

    with path.open(newline="", encoding="utf-8-sig") as handle:
        reader = csv.DictReader(handle)
        columns = [c for c in NAME_COLUMNS if c in (reader.fieldnames or [])]
        if not columns:
            sys.exit(f"{path} has none of {NAME_COLUMNS}")
        seen: dict[str, str] = {}
        for row in reader:
            for column in columns:
                raw = (row.get(column) or "").strip()
                key = normalise_practitioner_name(raw)
                if key and key not in seen:
                    seen[key] = raw
                if raw:
                    break
    return list(seen.values())


async def _queue(http, tenant_id: str, source_system: str, names: list[str], plan: Plan) -> None:
    """Open a review queue entry for each name. Asking twice changes nothing."""
    for name in names:
        response = await send(
            http,
            "POST",
            f"/provider-aliases?tenant_id={tenant_id}",
            json={"source_system": source_system, "source_value": name},
        )
        if response.status_code == 201:
            plan.created.append(name)
        else:
            plan.failed.append(f"{name}: {response.status_code} {response.text[:120]}")


async def _pages(http, url: str) -> list[dict]:
    items: list[dict] = []
    page = 1
    while True:
        response = await send(http, "GET", f"{url}&page={page}&limit={PAGE}")
        response.raise_for_status()
        body = response.json()
        items.extend(body["items"])
        if not body.get("has_more"):
            return items
        page += 1


async def _provider_ids(http, tenant_id: str) -> dict[str, list[str]]:
    from app.domain.services.provider_alias_normalisation import normalise_practitioner_name

    index: dict[str, list[str]] = {}
    for provider in await _pages(http, f"/providers?tenant_id={tenant_id}"):
        key = normalise_practitioner_name(provider["display_name"])
        if key:
            index.setdefault(key, []).append(provider["id"])
    return index


async def _applied_ids(http, tenant_id: str, batch_id: str) -> dict[str, list[str]]:
    """Normalised workbook name -> the practitioners applying the batch created."""
    index: dict[str, list[str]] = {}
    for row in await _pages(http, f"/practitioner-imports/{batch_id}/rows?tenant_id={tenant_id}"):
        provider_id = row.get("imported_provider_id")
        if provider_id and row.get("normalized_name"):
            index.setdefault(row["normalized_name"], []).append(provider_id)
    return index


def _decide(
    alias: dict,
    applied: dict[str, list[str]],
    sheet: dict[str, str],
    providers: dict[str, list[str]],
) -> tuple[str | None, str]:
    """Return the practitioner this alias names, and why, or None and the reason."""
    from app.domain.services.provider_alias_normalisation import normalise_practitioner_name

    normalized = alias["normalized_value"]
    from_batch = applied.get(normalized, [])
    if len(from_batch) == 1:
        return from_batch[0], "the import batch created this practitioner from this row"
    if from_batch:
        return None, f"the batch created {len(from_batch)} practitioners from this name"

    canonical = sheet.get(normalized)
    if canonical is None:
        return None, "no batch row and no entry in the reviewed mapping"
    candidates = providers.get(normalise_practitioner_name(canonical), [])
    if len(candidates) == 1:
        return candidates[0], f"the reviewed mapping gives {canonical!r}"
    if candidates:
        return None, f"{canonical!r} matches {len(candidates)} practitioners"
    return None, f"the mapping gives {canonical!r}, which is not a practitioner here"


async def run(
    tenant_id: str,
    batch_id: str,
    workbook: Path | None,
    sheet: str,
    source_system: str | None,
    names_file: Path | None,
    apply: bool,
) -> int:
    from httpx import ASGITransport, AsyncClient

    from app.core.security import TokenData, get_current_user, get_current_user_optional
    from app.main import app

    actor = TokenData(user_id=os.environ["IMPORT_ACTOR_ID"], tenant_id=tenant_id, role="Admin")
    app.dependency_overrides[get_current_user] = lambda: actor
    app.dependency_overrides[get_current_user_optional] = lambda: actor

    reviewed = _mapping(workbook, sheet)
    names = _source_names(names_file)
    plan = Plan()
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://import", timeout=300
    ) as http:
        if source_system and names:
            if apply:
                await _queue(http, tenant_id, source_system, names, plan)
            else:
                print(f"would queue {len(names)} names under {source_system!r}")
        applied = await _applied_ids(http, tenant_id, batch_id)
        providers = await _provider_ids(http, tenant_id)
        aliases = await _pages(http, f"/provider-aliases?tenant_id={tenant_id}&state=Unmapped")
        print(
            f"{len(aliases)} unmapped aliases, {len(applied)} applied batch names, "
            f"{len(reviewed)} reviewed mappings"
        )
        for alias in aliases:
            provider_id, why = _decide(alias, applied, reviewed, providers)
            label = f"{alias['source_value']}: {why}"
            if provider_id is None:
                plan.skipped.append(label)
                continue
            if not apply:
                plan.updated.append(label)
                continue
            response = await send(
                http,
                "POST",
                f"/provider-aliases/{alias['id']}/resolve?tenant_id={tenant_id}",
                json={"provider_id": provider_id},
            )
            if response.status_code == 200:
                plan.updated.append(label)
            else:
                plan.failed.append(
                    f"{alias['source_value']}: {response.status_code} {response.text[:120]}"
                )
    return report(apply, [("aliases", plan)])


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--tenant-id", required=True)
    parser.add_argument("--batch-id", required=True, help="Applied practitioner import batch")
    parser.add_argument("--mapping", type=Path, help="Workbook holding the reviewed name sheet")
    parser.add_argument("--sheet", default="Counselors")
    parser.add_argument("--source-system", help="Queue --names under this source system first")
    parser.add_argument("--names", type=Path, help="Extract whose practitioner names to queue")
    parser.add_argument("--apply", action="store_true", help="Write. Without it, plan only.")
    args = parser.parse_args()
    if not os.environ.get("IMPORT_ACTOR_ID"):
        sys.exit("IMPORT_ACTOR_ID must name the admin the resolutions are recorded against.")
    os.environ.setdefault("PYTHONWARNINGS", "ignore")
    if bool(args.source_system) != bool(args.names):
        sys.exit("--source-system and --names are used together or not at all.")
    return asyncio.run(
        run(
            args.tenant_id,
            args.batch_id,
            args.mapping,
            args.sheet,
            args.source_system,
            args.names,
            args.apply,
        )
    )


if __name__ == "__main__":
    raise SystemExit(main())
