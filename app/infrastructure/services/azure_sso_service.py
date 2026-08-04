"""
Azure AD SSO Service

Handles the OAuth2/OIDC Authorization Code flow with Microsoft Entra ID.
Wraps MSAL to build the login redirect URL and exchange the callback code
for verified identity claims.

State is a self-contained HMAC-signed token (nonce + expiry) — no server-side
session storage required.
"""

import base64
import hashlib
import hmac
import secrets
import time
from dataclasses import dataclass

import msal

from app.core.config import settings


@dataclass
class AzureClaims:
    """Verified identity claims extracted from an Azure AD id_token."""

    oid: str  # Object ID — immutable, unique per user per Azure directory
    tid: str  # Tenant ID — the employer's Azure AD directory
    email: str  # Preferred username / email
    name: str | None = None


class AzureSSOService:
    """
    Stateless service for Azure AD SSO.

    One instance per request is fine — the MSAL app object is cheap.
    Raises RuntimeError if Azure env vars are not configured.
    """

    _STATE_TTL_SECONDS = 300  # 5-minute window for the OAuth round-trip
    # MSAL Python auto-appends openid + profile + offline_access; passing them
    # explicitly raises "reserved scope" ValueError. Only list resource scopes.
    _SCOPES: list[str] = []
    # Use /organizations so only work/school accounts can log in (not personal MSAs)
    _AUTHORITY = "https://login.microsoftonline.com/organizations"

    def _require_config(self) -> None:
        if not settings.azure_sso_configured:
            raise RuntimeError(
                "Azure SSO is not configured. Set AZURE_CLIENT_ID, AZURE_CLIENT_SECRET, "
                "AZURE_REDIRECT_URI, and AZURE_FRONTEND_REDIRECT_URI."
            )

    def _get_msal_app(self) -> msal.ConfidentialClientApplication:
        return msal.ConfidentialClientApplication(
            client_id=settings.AZURE_CLIENT_ID,
            client_credential=settings.AZURE_CLIENT_SECRET,
            authority=self._AUTHORITY,
        )

    # -------------------------------------------------------------------------
    # Public API
    # -------------------------------------------------------------------------

    def build_auth_url(self) -> tuple[str, str]:
        """
        Build the Microsoft login redirect URL.

        Returns:
            (auth_url, state) — redirect the browser to auth_url; the state
            value is already embedded in auth_url by MSAL.
        """
        self._require_config()
        state = self._create_state()
        app = self._get_msal_app()
        auth_url = app.get_authorization_request_url(
            scopes=self._SCOPES,
            redirect_uri=settings.AZURE_REDIRECT_URI,
            state=state,
        )
        return auth_url, state

    def exchange_code(self, code: str, state: str) -> AzureClaims:
        """
        Verify the CSRF state and exchange the authorization code for claims.

        Args:
            code: The authorization code from Azure's callback query string
            state: The state parameter from Azure's callback query string

        Returns:
            Verified AzureClaims with oid, tid, email

        Raises:
            ValueError: If state is invalid/expired or token exchange fails
        """
        self._require_config()
        self._verify_state(state)

        app = self._get_msal_app()
        result = app.acquire_token_by_authorization_code(
            code=code,
            scopes=self._SCOPES,
            redirect_uri=settings.AZURE_REDIRECT_URI,
        )

        if "error" in result:
            raise ValueError(
                f"Azure token exchange failed: {result.get('error_description', result.get('error'))}"
            )

        claims = result.get("id_token_claims") or {}
        oid = claims.get("oid")
        tid = claims.get("tid")
        # Azure sends the UPN as preferred_username; fall back to email claim
        email = claims.get("preferred_username") or claims.get("email") or claims.get("upn")

        if not oid or not tid or not email:
            raise ValueError(
                "Azure token is missing required claims (oid, tid, preferred_username)"
            )

        return AzureClaims(
            oid=str(oid),
            tid=str(tid),
            email=str(email).lower().strip(),
            name=claims.get("name"),
        )

    # -------------------------------------------------------------------------
    # State signing (HMAC-SHA256, self-contained, no server storage)
    # -------------------------------------------------------------------------

    def _create_state(self) -> str:
        nonce = secrets.token_urlsafe(16)
        exp = int(time.time()) + self._STATE_TTL_SECONDS
        payload = f"{nonce}:{exp}"
        sig = self._sign(payload)
        raw = f"{payload}:{sig}"
        return base64.urlsafe_b64encode(raw.encode()).decode()

    def _verify_state(self, state: str) -> None:
        try:
            decoded = base64.urlsafe_b64decode(state.encode()).decode()
            # Format: nonce:exp:signature  — nonce may contain url-safe chars but not ':'
            parts = decoded.split(":")
            if len(parts) != 3:
                raise ValueError("malformed state")
            nonce, exp_str, sig = parts
            exp = int(exp_str)
            if time.time() > exp:
                raise ValueError("state has expired")
            payload = f"{nonce}:{exp_str}"
            expected = self._sign(payload)
            if not hmac.compare_digest(sig, expected):
                raise ValueError("state signature mismatch")
        except ValueError:
            raise
        except Exception as exc:
            raise ValueError(f"invalid state: {exc}") from exc

    def _sign(self, payload: str) -> str:
        return hmac.new(
            settings.SECRET_KEY.encode(),
            payload.encode(),
            hashlib.sha256,
        ).hexdigest()
