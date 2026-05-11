"""
Dump the FastAPI app's OpenAPI schema to schema/openapi.json.

Run from the evexia_bk repo root:
    .venv/bin/python scripts/dump_openapi.py

Used by the FE codegen pipeline (openapi-typescript) to keep types in sync
with the BE wire contract.
"""

from __future__ import annotations

import json
from pathlib import Path


def main() -> None:
    # Lazy import so importing this module doesn't trigger app boot.
    from app.main import app

    schema = app.openapi()
    out = Path(__file__).resolve().parent.parent / "schema" / "openapi.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(schema, indent=2, sort_keys=True) + "\n")
    print(f"Wrote {out} ({len(json.dumps(schema))} bytes, {len(schema.get('paths', {}))} paths)")


if __name__ == "__main__":
    main()
