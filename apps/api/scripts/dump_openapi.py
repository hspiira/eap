"""
Dump the FastAPI app's OpenAPI schema to schema/openapi.json.

Run from the backend repo root:
    uv run python scripts/dump_openapi.py

Used by the FE codegen pipeline (openapi-typescript) to keep types in sync
with the BE wire contract.
"""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path

# Running as a script puts scripts/ on sys.path, not the repo root.
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

CONTRACT_TITLE = "Evexía"
CONTRACT_VERSION = "0.1.0"


def main() -> None:
    # Refuse to run under ENVIRONMENT=test: the app title and version come from
    # settings, so a test run bakes "EAP Test" / "0.0.0-test" into the committed
    # contract.
    if os.environ.get("ENVIRONMENT") == "test":
        raise SystemExit(
            "Refusing to dump the schema with ENVIRONMENT=test - it would write "
            "test app metadata into schema/openapi.json. Unset ENVIRONMENT."
        )

    # Lazy import so importing this module doesn't trigger app boot.
    from app.main import app

    schema = app.openapi()

    # Pinned, not read from settings: otherwise the dump varies with the
    # developer's APP_NAME and the frontend's exact-diff check fails.
    schema["info"] = dict(schema.get("info", {})) | {
        "title": CONTRACT_TITLE,
        "version": CONTRACT_VERSION,
    }
    out = Path(__file__).resolve().parent.parent / "schema" / "openapi.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(schema, indent=2, sort_keys=True) + "\n")
    print(f"Wrote {out} ({len(json.dumps(schema))} bytes, {len(schema.get('paths', {}))} paths)")


if __name__ == "__main__":
    main()
