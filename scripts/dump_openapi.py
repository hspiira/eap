"""
Dump the FastAPI app's OpenAPI schema to schema/openapi.json.

Run from the evexia_bk repo root:
    .venv/bin/python scripts/dump_openapi.py

Used by the FE codegen pipeline (openapi-typescript) to keep types in sync
with the BE wire contract.
"""

from __future__ import annotations

import json
import os
from pathlib import Path


def main() -> None:
    # Refuse to run under ENVIRONMENT=test: the app title and version come from
    # settings, so a test run bakes "EAP Test" / "0.0.0-test" into the committed
    # contract.
    if os.environ.get("ENVIRONMENT") == "test":
        raise SystemExit(
            "Refusing to dump the schema with ENVIRONMENT=test — it would write "
            "test app metadata into schema/openapi.json. Unset ENVIRONMENT."
        )

    # Lazy import so importing this module doesn't trigger app boot.
    from app.main import app

    schema = app.openapi()
    out = Path(__file__).resolve().parent.parent / "schema" / "openapi.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(schema, indent=2, sort_keys=True) + "\n")
    print(f"Wrote {out} ({len(json.dumps(schema))} bytes, {len(schema.get('paths', {}))} paths)")


if __name__ == "__main__":
    main()
