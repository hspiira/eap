"""Regression coverage for client alias normalization."""

from app.shared.utils.client_alias import normalize_client_alias


def test_normalize_client_alias_collapses_spacing_and_case() -> None:
    assert normalize_client_alias("  ABSA   Bank Uganda Limited ") == "absa bank uganda limited"


def test_normalize_client_alias_returns_empty_for_blank_input() -> None:
    assert normalize_client_alias(" \t\n") == ""
