"""Resolve a database URL for a test that needs real PostgreSQL.

A missing URL normally skips, which keeps a local run without a database
usable. Under REQUIRE_DATABASE_TESTS it fails instead: CI sets that so a
release gate cannot pass on tests that silently never ran.
"""

import os

import pytest
from sqlalchemy.engine import make_url

LOCAL_HOSTS = {"localhost", "127.0.0.1", "::1"}


def require_local_database(variable: str) -> str:
    raw = os.environ.get(variable)
    if not raw:
        message = f"Set {variable} to local PostgreSQL"
        if os.environ.get("REQUIRE_DATABASE_TESTS"):
            pytest.fail(f"{message}. REQUIRE_DATABASE_TESTS forbids skipping it.")
        pytest.skip(message)
    if make_url(raw).host not in LOCAL_HOSTS:
        pytest.fail(f"{variable} must point at local PostgreSQL")
    return raw
