"""Normalization helpers for tenant-scoped client aliases."""

import re


def normalize_client_alias(value: str) -> str:
    """Normalize an alias for matching and uniqueness checks."""
    return re.sub(r"\s+", " ", value.strip()).casefold()
