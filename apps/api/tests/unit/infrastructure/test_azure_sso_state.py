"""
OAuth state-token integrity for the Azure SSO flow.

The signed state proves "this server minted this token recently". On its own it
does NOT prove "this browser started this flow", so an attacker could begin
their own login, capture the resulting code+state, and feed it to a victim's
browser, silently signing the victim into the attacker's account (login CSRF).
Binding the state to a nonce cookie issued at /azure/login closes that.

These exercise the state helpers directly: the full flow needs live Azure
credentials, but state signing only needs SECRET_KEY.
"""

import base64
import time

import pytest

from app.infrastructure.services.azure_sso_service import AzureSSOService


@pytest.fixture
def sso() -> AzureSSOService:
    return AzureSSOService()


def _decode(state: str) -> tuple[str, str, str]:
    nonce, exp, sig = base64.urlsafe_b64decode(state.encode()).decode().split(":")
    return nonce, exp, sig


class TestStateBinding:
    def test_create_returns_state_and_matching_nonce(self, sso):
        state, nonce = sso._create_state()
        assert _decode(state)[0] == nonce

    def test_accepts_matching_nonce(self, sso):
        state, nonce = sso._create_state()
        sso._verify_state(state, nonce)  # must not raise

    def test_rejects_foreign_nonce(self, sso):
        """The login-CSRF case: valid signature, but a different browser's flow."""
        state, _ = sso._create_state()
        _, attacker_nonce = sso._create_state()
        with pytest.raises(ValueError, match="not issued to this browser"):
            sso._verify_state(state, attacker_nonce)

    @pytest.mark.parametrize("missing", [None, ""])
    def test_rejects_absent_nonce(self, sso, missing):
        """No cookie means the browser never started this flow; fail closed."""
        state, _ = sso._create_state()
        with pytest.raises(ValueError, match="not issued to this browser"):
            sso._verify_state(state, missing)

    def test_nonces_are_unique_per_flow(self, sso):
        assert sso._create_state()[1] != sso._create_state()[1]


class TestStateIntegrity:
    def test_rejects_tampered_signature(self, sso):
        state, nonce = sso._create_state()
        n, exp, sig = _decode(state)
        forged = f"{n}:{exp}:{'0' * len(sig)}"
        tampered = base64.urlsafe_b64encode(forged.encode()).decode()
        with pytest.raises(ValueError, match="signature mismatch"):
            sso._verify_state(tampered, nonce)

    def test_rejects_expired_state(self, sso, monkeypatch):
        state, nonce = sso._create_state()
        # Capture the real clock before patching; referencing time.time() from
        # inside the replacement would recurse into itself.
        future = time.time() + sso._STATE_TTL_SECONDS + 60
        monkeypatch.setattr(time, "time", lambda: future)
        with pytest.raises(ValueError, match="expired"):
            sso._verify_state(state, nonce)

    @pytest.mark.parametrize("bad", ["not-base64!!", "", "YWJj"])
    def test_rejects_malformed_state(self, sso, bad):
        with pytest.raises(ValueError):
            sso._verify_state(bad, "any-nonce")
