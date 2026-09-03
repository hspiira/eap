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

# Running as a script puts scripts/ on sys.path, not the repo root, so `app` would
# not import. Add the root so this works without the caller setting PYTHONPATH.
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

# The published contract's identity. Deliberately not read from settings — see main().
CONTRACT_TITLE = "Evexía"
CONTRACT_VERSION = "0.1.0"


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

    # app.openapi() takes title/version from settings, which read .env, so the
    # output otherwise varies with whatever APP_NAME the developer running this
    # happens to have set ("Evexia" vs "Evexía"). The frontend gates on an exact
    # diff of this file, so pin the identity to constants and keep the dump a
    # pure function of the routes.
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
