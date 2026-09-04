"""Webhook HMAC signature tests (Phase 3 #D-Survey)."""

import pytest

from app.core.webhook_signature import compute_signature, verify_signature

SECRET = "test-secret-with-sufficient-length-padding"


class TestVerifySignature:
    def test_round_trip(self):
        body = b'{"hello":"world"}'
        sig = compute_signature(SECRET, body)
        assert verify_signature(SECRET, body, sig) is True

    def test_sha256_prefix_accepted(self):
        body = b'{"a":1}'
        sig = compute_signature(SECRET, body)
        assert verify_signature(SECRET, body, f"sha256={sig}") is True

    def test_wrong_secret_rejected(self):
        body = b'{"a":1}'
        sig = compute_signature(SECRET, body)
        assert verify_signature("not-the-secret", body, sig) is False

    def test_tampered_body_rejected(self):
        body = b'{"a":1}'
        sig = compute_signature(SECRET, body)
        assert verify_signature(SECRET, b'{"a":2}', sig) is False

    def test_missing_header_rejected(self):
        assert verify_signature(SECRET, b"x", None) is False
        assert verify_signature(SECRET, b"x", "") is False

    def test_garbage_header_rejected(self):
        assert verify_signature(SECRET, b"x", "not-hex") is False


class TestNonAsciiHeader:
    """A hostile header must fail closed, not raise.

    hmac.compare_digest refuses str operands containing non-ASCII characters,
    and headers reach the handler as latin-1 decoded text, so any byte above
    0x7f in X-Webhook-Signature used to raise TypeError. On a public
    unauthenticated webhook that surfaced as a 500 rather than the uniform 401
    the caller documents.
    """

    @pytest.mark.parametrize(
        "header",
        [
            "\xff\xfe",
            "sha256=\xff",
            "\u2014" * 64,  # em dash
            "café",
            "sha256=" + "é" * 64,
            "\u200b" * 8,  # zero-width space
        ],
    )
    def test_non_ascii_header_is_rejected_without_raising(self, header: str) -> None:
        assert verify_signature(SECRET, b"x", header) is False

    def test_valid_signature_with_a_non_ascii_suffix_is_rejected(self) -> None:
        body = b'{"a":1}'
        sig = compute_signature(SECRET, body)
        assert verify_signature(SECRET, body, sig + "é") is False

    def test_ascii_behaviour_is_unchanged(self) -> None:
        body = b'{"a":1}'
        sig = compute_signature(SECRET, body)
        assert verify_signature(SECRET, body, sig) is True
        assert verify_signature(SECRET, body, sig.upper()) is False
