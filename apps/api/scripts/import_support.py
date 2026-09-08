"""Shared pieces for the reference-data importers.

Each importer loads one extract into an environment through the real API. What
they have in common is a plan they can print without writing, and a request
helper that waits out the rate limiter instead of failing half way.
"""

from __future__ import annotations

import asyncio


class Plan:
    """What one pass did, or would do.

    A plain class, not a dataclass: the script-runnable check execs importer
    modules with a synthetic globals dict, and `@dataclass` needs annotations
    that exec does not provide.
    """

    def __init__(self) -> None:
        self.created: list[str] = []
        self.updated: list[str] = []
        self.unchanged: list[str] = []
        self.skipped: list[str] = []
        self.failed: list[str] = []

    def line(self, label: str) -> str:
        return (
            f"{label:18} create {len(self.created):3}  update {len(self.updated):3}  "
            f"same {len(self.unchanged):3}  skip {len(self.skipped):3}  fail {len(self.failed):3}"
        )


async def send(http, method: str, url: str, **kwargs):
    """One request, waiting out the rate limiter rather than failing the import.

    A reference-data load is hundreds of writes and will trip any sane
    per-client limit. Retrying on the server's own retry-after keeps the
    importer honest: it does not raise the limit, disable it, or write around it.
    """
    for attempt in range(6):
        response = await http.request(method, url, **kwargs)
        if response.status_code != 429:
            return response
        try:
            wait = float(response.json().get("retry_after", 5))
        except (ValueError, AttributeError):
            wait = 5.0
        print(f"    rate limited, waiting {wait:.0f}s (attempt {attempt + 1})", flush=True)
        await asyncio.sleep(min(wait, 60) + 1)
    return response


def report(apply: bool, sections: list[tuple[str, Plan]]) -> int:
    print("\n" + ("APPLIED" if apply else "PLAN ONLY, nothing written"))
    for label, plan in sections:
        print("  " + plan.line(label))
    for label, plan in sections:
        for note in plan.skipped + plan.failed:
            print(f"  {label}: {note}")
    return 1 if any(plan.failed for _, plan in sections) else 0
