"""Webhook HMAC signature tests (Phase 3 #D-Survey)."""

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
