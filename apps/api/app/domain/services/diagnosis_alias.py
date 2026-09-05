"""Normalisation for legacy diagnosis strings.

The source data spells one concept many ways: 53 raw values for 29 buckets in
the reference extract, with case, underscores, doubled spaces and trailing
whitespace all varying. Lookups key on the normalised form so those collapse to
one entry. See apps/api/docs/SERVICES_MODULE.md section 3.3.
"""

from __future__ import annotations

import re

_NON_ALNUM = re.compile(r"[^a-z0-9]+")


def normalise_diagnosis_value(raw: str) -> str:
    """Casefold, collapse punctuation and whitespace, and trim.

    ``Family___Relationship`` and ``Family &  Relationship`` both give
    ``family relationship``.
    """
    return _NON_ALNUM.sub(" ", raw.casefold()).strip()
