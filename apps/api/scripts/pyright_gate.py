"""Pyright result gate.

Runs the strict gate per package: parses pyright's JSON output and fails the
build only when errors are found inside one of the supplied root paths.
Useful while ratcheting strict mode out of ``app/domain`` into the rest of
the codebase one package at a time.

Usage:
    pyright_gate.py <pyright_json_path> <gated_root> [<gated_root> ...]
    pyright_gate.py <pyright_json_path> --report-only

The first form fails (exit 1) when *any* error's file path starts with one of
the gated roots. The second form prints a per-package error count without
failing - useful for keeping the rest of the project visible without forcing
a gate yet.
"""

from __future__ import annotations

import json
import sys
from collections import Counter
from pathlib import Path


def _load(path: Path) -> dict[str, object]:
    with path.open("r", encoding="utf-8") as fh:
        return json.load(fh)


def _file_to_package(file_path: str, repo_root: Path) -> str:
    try:
        rel = Path(file_path).resolve().relative_to(repo_root)
    except ValueError:
        return "<external>"
    parts = rel.parts
    if len(parts) <= 2:
        return rel.as_posix()
    return "/".join(parts[:2])


def _is_under_root(file_path: str, gated_roots: list[Path]) -> bool:
    resolved = Path(file_path).resolve()
    for root in gated_roots:
        try:
            resolved.relative_to(root)
            return True
        except ValueError:
            continue
    return False


def main(argv: list[str]) -> int:
    if len(argv) < 2:
        print(__doc__, file=sys.stderr)
        return 2
    payload = _load(Path(argv[0]))
    diagnostics = payload.get("generalDiagnostics", [])
    if not isinstance(diagnostics, list):
        print("Unexpected pyright JSON shape", file=sys.stderr)
        return 2
    errors = [d for d in diagnostics if isinstance(d, dict) and d.get("severity") == "error"]
    report_only = argv[1] == "--report-only"
    repo_root = Path.cwd().resolve()

    by_package: Counter[str] = Counter()
    for d in errors:
        file_path = str(d.get("file", ""))
        by_package[_file_to_package(file_path, repo_root)] += 1

    if report_only:
        print(f"Pyright total errors: {len(errors)}")
        for pkg, count in by_package.most_common():
            print(f"  {pkg:40s} {count:6d}")
        return 0

    gated_roots = [(Path.cwd() / arg).resolve() for arg in argv[1:]]
    gated_errors = [d for d in errors if _is_under_root(str(d.get("file", "")), gated_roots)]
    if gated_errors:
        print(
            f"Pyright gate FAILED: {len(gated_errors)} errors under "
            f"{', '.join(str(r.relative_to(repo_root)) for r in gated_roots)}",
            file=sys.stderr,
        )
        for d in gated_errors[:50]:
            file_path = d.get("file", "")
            line = d.get("range", {}).get("start", {}).get("line", 0)
            print(
                f"  {file_path}:{int(line) + 1} - {d.get('message', '')}",
                file=sys.stderr,
            )
        if len(gated_errors) > 50:
            print(f"  ... {len(gated_errors) - 50} more", file=sys.stderr)
        return 1
    print("Pyright gate OK for " + ", ".join(str(r.relative_to(repo_root)) for r in gated_roots))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
