"""Load clients and their aliases into an environment.

Runs against the real API through ASGI, so every row passes the same
validation, authorisation and audit a human write would. Only authentication is
stubbed, as it is for any CLI importer.

Identity is the client's name or any alias already resolving to it, so a client
created under one spelling is recognised on the next run rather than duplicated.
Aliases are merged, never replaced: the endpoint takes the full set, so an alias
added in the environment survives an import that does not know about it.

    uv run python scripts/import_clients.py --tenant-id <id>            # plan
    uv run python scripts/import_clients.py --tenant-id <id> --apply    # write
"""

from __future__ import annotations

import argparse
import asyncio
import html
import json
import os
import re
import sys
from pathlib import Path

SCRIPTS_DIR = Path(__file__).resolve().parent
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

API_ROOT = Path(__file__).resolve().parent.parent
if str(API_ROOT) not in sys.path:
    sys.path.insert(0, str(API_ROOT))

from import_support import Plan, report, send  # noqa: E402

SOURCE = API_ROOT / "data" / "taxonomy" / "clients.json"


def _normalise(name: str) -> str:
    return re.sub(r"[^a-z0-9]+", " ", name.lower()).strip()


async def run(tenant_id: str, apply: bool) -> int:
    from httpx import ASGITransport, AsyncClient

    from app.core.security import TokenData, get_current_user, get_current_user_optional
    from app.main import app

    if not SOURCE.exists():
        sys.exit(
            f"{SOURCE} is missing. Run:\n"
            "  uv run --with openpyxl python scripts/extract_companies.py --workbook <path>"
        )
    wanted = json.loads(SOURCE.read_text())

    actor = TokenData(user_id="client-import", tenant_id=tenant_id, role="Admin")
    app.dependency_overrides[get_current_user] = lambda: actor
    app.dependency_overrides[get_current_user_optional] = lambda: actor

    clients_plan, aliases_plan = Plan(), Plan()
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://import", timeout=120
    ) as http:
        existing = await _existing(http, tenant_id)
        codes = {row["code"] for row in existing.values() if row.get("code")}
        for row in wanted:
            await _client(http, tenant_id, row, existing, codes, clients_plan, aliases_plan, apply)

    return report(apply, [("clients", clients_plan), ("aliases", aliases_plan)])


async def _existing(http, tenant_id: str) -> dict[str, dict]:
    """Every client in the tenant, keyed by its name and by each of its aliases."""
    found: dict[str, dict] = {}
    page = 1
    while True:
        response = await send(http, "GET", f"/clients/?tenant_id={tenant_id}&page={page}&limit=100")
        body = response.json()
        items = body.get("items", []) if isinstance(body, dict) else []
        for row in items:
            found[_normalise(row["name"])] = row
            # Also index the unescaped name, so a row corrupted by the old
            # sanitiser ("I&amp;M Bank") is recognised as the client it is
            # rather than matched as absent and duplicated.
            found.setdefault(_normalise(html.unescape(row["name"])), row)
            for alias in row.get("aliases", []):
                found.setdefault(_normalise(alias), row)
        if not isinstance(body, dict) or not body.get("has_more"):
            return found
        page += 1


async def _client(
    http,
    tenant_id: str,
    row: dict,
    existing: dict[str, dict],
    codes: set[str],
    clients_plan: Plan,
    aliases_plan: Plan,
    apply: bool,
) -> None:
    keys = [_normalise(row["name"])] + [_normalise(a) for a in row["aliases"]]
    current = next((existing[key] for key in keys if key in existing), None)

    if current is None:
        code = row["code"]
        while code in codes:
            code = (code[:4] + "X")[:5] if len(code) >= 5 else code + "X"
        codes.add(code)
        if not apply:
            clients_plan.created.append(row["name"])
        else:
            response = await send(
                http,
                "POST",
                f"/clients/?tenant_id={tenant_id}",
                json={"name": row["name"], "code": code, "contact_info": {}},
            )
            if response.status_code != 201:
                clients_plan.failed.append(
                    f"{row['name']}: {response.status_code} {response.text[:120]}"
                )
                return
            current = response.json()
            existing[_normalise(row["name"])] = current
            clients_plan.created.append(row["name"])
        if not apply:
            if row["aliases"]:
                aliases_plan.created.append(f"{row['name']}: +{len(row['aliases'])}")
            return
    elif html.unescape(current["name"]) == row["name"] != current["name"]:
        # The old sanitiser HTML-escaped names on the way in, so "I&M Bank" was
        # stored "I&amp;M Bank". Repaired only when unescaping the stored name
        # reproduces the wanted one exactly; anything else is a different name
        # and is left alone.
        if not apply:
            clients_plan.updated.append(f"{current['name']} -> {row['name']} (unescape)")
        else:
            response = await send(
                http,
                "PATCH",
                f"/clients/{current['id']}?tenant_id={tenant_id}",
                json={"name": row["name"]},
            )
            if response.status_code != 200:
                clients_plan.failed.append(
                    f"{row['name']}: repair {response.status_code} {response.text[:120]}"
                )
                return
            current = response.json()
            existing[_normalise(row["name"])] = current
            clients_plan.updated.append(f"{row['name']} (unescaped)")
    else:
        clients_plan.unchanged.append(row["name"])
        if _normalise(current["name"]) != _normalise(row["name"]):
            clients_plan.skipped.append(
                f"{row['name']}: already present as {current['name']!r} through an alias; "
                "left under its existing name"
            )

    await _aliases(http, tenant_id, row, current, existing, aliases_plan, apply)


async def _aliases(
    http,
    tenant_id: str,
    row: dict,
    current: dict,
    existing: dict[str, dict],
    plan: Plan,
    apply: bool,
) -> None:
    """Merge the workbook's aliases into whatever the client already has.

    The endpoint replaces the whole set, so sending only the workbook's would
    silently drop an alias someone added in the environment.
    """
    have = list(current.get("aliases", []))
    have_keys = {_normalise(alias) for alias in have}
    canonical = _normalise(current["name"])

    additions = []
    for alias in row["aliases"]:
        key = _normalise(alias)
        if key == canonical or key in have_keys:
            continue
        owner = existing.get(key)
        if owner is not None and owner["id"] != current["id"]:
            plan.skipped.append(
                f"{alias!r}: already resolves to {owner['name']!r}, not {current['name']!r}"
            )
            continue
        additions.append(alias)
        have_keys.add(key)

    if not additions:
        plan.unchanged.append(current["name"])
        return
    if not apply:
        plan.updated.append(f"{current['name']}: +{len(additions)}")
        return

    response = await send(
        http,
        "PATCH",
        f"/clients/{current['id']}/aliases?tenant_id={tenant_id}",
        json={"aliases": have + additions},
    )
    if response.status_code != 200:
        plan.failed.append(f"{current['name']}: {response.status_code} {response.text[:140]}")
        return
    for alias in additions:
        existing[_normalise(alias)] = current
    plan.updated.append(f"{current['name']}: +{len(additions)}")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--tenant-id", required=True, help="Tenant that owns the clients")
    parser.add_argument("--apply", action="store_true", help="Write. Without it, plan only.")
    args = parser.parse_args()
    os.environ.setdefault("PYTHONWARNINGS", "ignore")
    return asyncio.run(run(args.tenant_id, args.apply))


if __name__ == "__main__":
    raise SystemExit(main())
