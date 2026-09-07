"""Replay keys, and the two ways a staged row stops claiming its source row.

A replay key says "this source row has been imported", and exactly one staged
row may hold it, so re-importing an extract cannot write the same session
twice. Two kinds of row hold no claim:

- one that gave its key up, because the batch was abandoned or because a later
  staging of the same file re-judged the source row it never imported;
- one that never took the key, because an imported row already holds it.

Both keep their original key inside, so what the row staged stays readable, and
both name the batch the key belongs to.
"""

from __future__ import annotations

RELEASED_PREFIX = "released:"
DUPLICATE_PREFIX = "duplicate:"


def deferred_key(prefix: str, batch_id: str, replay_key: str) -> str:
    """A key that points at `batch_id` instead of claiming the source row."""
    return f"{prefix}{batch_id}:{replay_key}"
