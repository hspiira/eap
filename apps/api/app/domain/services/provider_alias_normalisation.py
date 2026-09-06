"""Normalisation for practitioner names arriving from a source system.

Follows `diagnosis_alias.normalise_diagnosis_value`, with two differences that
decision 5 requires. Titles are stripped, because "Dr Alice Nakato" and "Alice
Nakato" are the same source spelling for lookup purposes. And the result is
never treated as identity: it only groups candidates for a person to reconcile.
"""

from __future__ import annotations

import re

_NON_ALNUM = re.compile(r"[^a-z0-9]+")

_TITLES = frozenset(
    {"dr", "doctor", "mr", "mrs", "ms", "miss", "prof", "professor", "rev", "sr", "counsellor"}
)


def normalise_practitioner_name(raw: str) -> str:
    """Casefold, drop punctuation, strip leading titles, and collapse whitespace.

    Returns an empty string when nothing usable remains, which the caller must
    treat as a missing name rather than as a match.
    """
    collapsed = _NON_ALNUM.sub(" ", raw.casefold()).strip()
    if not collapsed:
        return ""
    parts = collapsed.split()
    while parts and parts[0] in _TITLES:
        parts.pop(0)
    return " ".join(parts)


def is_usable_name(raw: str) -> bool:
    """Whether a source value normalises to anything that could name a person."""
    return bool(normalise_practitioner_name(raw))
