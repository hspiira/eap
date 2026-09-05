"""
Azure AD SSO Routes

Split from auth.py (doc 10, god-file cleanup): these two routes are a
self-contained redirect flow (browser -> Microsoft -> callback) sharing no
helpers with the password-auth routes.
"""

import logging
from urllib.parse import quote

from fastapi import APIRouter, Cookie, Depends, Query, status
from fastapi.responses import RedirectResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import (
    get_refresh_token_repository,
    get_tenant_repository,
    get_user_repository,
)
from app.core.config import settings
from app.core.database import get_db
from app.core.security import COOKIE_ACCESS_TOKEN, COOKIE_REFRESH_TOKEN, create_token_response
from app.domain.enums import TenantStatus, UserStatus
from app.domain.exceptions import DomainError
from app.domain.repositories.tenant_repository import TenantRepository
from app.domain.repositories.user_repository import UserRepository
from app.domain.value_objects.core import Email
from app.infrastructure.repositories.refresh_token_repository import (
    RefreshTokenRepository,
)
from app.infrastructure.services.azure_sso_service import AzureSSOService
from app.shared.decorators import transactional
from app.shared.utils.generators import generate_cuid

router = APIRouter(prefix="/auth", tags=["authentication"])

logger = logging.getLogger(__name__)

# Ties the OAuth round-trip to the browser that began it (login-CSRF defence).
COOKIE_SSO_STATE = "evexia_sso_state"
# Matches AzureSSOService._STATE_TTL_SECONDS; the signed state expires anyway.
_SSO_STATE_COOKIE_MAX_AGE = 300


def _mask_email(email: str | None) -> str:
    """
    Redact the local part for logs: 'fred.hasibiri@minet.co.ug' -> 'f***@minet.co.ug'.

    Enough to correlate a failed login with a domain/tenant while keeping
    routine sign-ins from writing identifiable addresses into log storage.
    """
    if not email or "@" not in email:
        return "<none>"
    local, _, domain = email.partition("@")
    head = local[0] if local else ""
    return f"{head}***@{domain}"


@router.get(
    "/azure/login",
    status_code=status.HTTP_302_FOUND,
    summary="Initiate Azure AD SSO (redirects to Microsoft login)",
    include_in_schema=True,
)
async def azure_login() -> RedirectResponse:
    """
    Start the Azure AD OAuth2 flow.  No credentials required from the user.
    The browser is redirected to Microsoft's login page; after authentication
    Azure redirects back to /auth/azure/callback.

    Sets a short-lived HttpOnly nonce cookie; the callback requires it to match
    the nonce inside the signed state, proving the same browser started the flow.

    Redirects to the frontend error page when SSO is not configured.
    """
    if not settings.azure_sso_configured:
        error_url = f"{settings.AZURE_FRONTEND_REDIRECT_URI}?error={quote('Microsoft SSO is not configured on this server. Contact your administrator.')}"
        return RedirectResponse(error_url, status_code=status.HTTP_302_FOUND)
    sso = AzureSSOService()
    auth_url, nonce = sso.build_auth_url()
    response = RedirectResponse(auth_url, status_code=status.HTTP_302_FOUND)
    response.set_cookie(
        key=COOKIE_SSO_STATE,
        value=nonce,
        max_age=_SSO_STATE_COOKIE_MAX_AGE,
        path="/",
        secure=not settings.is_development,
        httponly=True,
        # 'lax' still sends the cookie on Microsoft's top-level GET redirect back
        # to the callback; 'strict' would drop it and break every SSO login.
        samesite="lax",
    )
    return response


@router.get(
    "/azure/callback",
    status_code=status.HTTP_302_FOUND,
    summary="Azure AD SSO callback (exchanges code for internal JWT)",
    include_in_schema=True,
)
@transactional()
async def azure_callback(
    code: str = Query(..., description="Authorization code from Azure"),
    state: str = Query(..., description="CSRF state from the login redirect"),
    sso_state_nonce: str | None = Cookie(default=None, alias=COOKIE_SSO_STATE),
    tenant_repo: TenantRepository = Depends(get_tenant_repository),
    user_repo: UserRepository = Depends(get_user_repository),
    refresh_token_repo: RefreshTokenRepository = Depends(get_refresh_token_repository),
    db: AsyncSession = Depends(get_db),
) -> RedirectResponse:
    """
    Azure redirects here after the user signs in.

    Flow:
    1. Verify CSRF state (HMAC-signed + bound to this browser's nonce cookie)
    2. Exchange code for Azure id_token
    3. Extract oid + tid + email from token claims
    4. Resolve Evexia tenant via tenants.azure_tenant_id == tid
    5. Find user by azure_oid (returning SSO user) or email (first-time link)
    6. Issue internal JWT (same claims as password login)
    7. Set HttpOnly cookies + redirect to AZURE_FRONTEND_REDIRECT_URI

    Every failure path returns a redirect carrying a user-facing ?error=
    message, never a raw 5xx, which would surface as a blank page.
    """

    def _error_redirect(message: str) -> RedirectResponse:
        url = f"{settings.AZURE_FRONTEND_REDIRECT_URI}?error={quote(message)}"
        response = RedirectResponse(url, status_code=status.HTTP_302_FOUND)
        # The flow is over either way; don't leave a usable nonce behind.
        response.delete_cookie(COOKIE_SSO_STATE, path="/")
        return response

    sso = AzureSSOService()

    try:
        claims = sso.exchange_code(code, state, expected_nonce=sso_state_nonce)
    except ValueError as exc:
        return _error_redirect(f"Authentication failed: {exc}")

    logger.info(
        "[azure-callback] received claims tid=%s email=%s oid=%s",
        claims.tid,
        _mask_email(claims.email),
        claims.oid,
    )
    tenant = await tenant_repo.get_by_azure_tenant_id(claims.tid)
    if not tenant:
        return _error_redirect(
            "Your organisation is not registered in Evexia. Contact your administrator."
        )
    if not tenant.azure_sso_enabled:
        return _error_redirect("Microsoft sign-in is not enabled for your organisation.")
    if tenant.status != TenantStatus.ACTIVE:
        return _error_redirect(
            f"Organisation account is {tenant.status.value.lower()}. Access denied."
        )

    # Resolve user: by OID first (returning user), then by email (first SSO login)
    user = await user_repo.get_by_azure_oid(claims.oid, tenant.id)
    if not user:
        # Azure UPNs are not always RFC-shaped addresses (B2B guests look like
        # `fred_gmail.com#EXT#@tenant.onmicrosoft.com`). Parsing outside a guard
        # would raise ValueError and surface as a 500 blank page rather than a
        # readable message.
        try:
            email = Email(claims.email)
        except ValueError:
            logger.warning(
                "[azure-callback] unusable email claim tid=%s email=%s oid=%s",
                claims.tid,
                _mask_email(claims.email),
                claims.oid,
            )
            return _error_redirect(
                "Your Microsoft account does not expose a usable email address. "
                "Contact your administrator."
            )

        user = await user_repo.get_by_email(email, tenant.id)
        if not user:
            return _error_redirect(
                "Your account has not been provisioned in Evexia. Contact your administrator."
            )
        # First-time Azure login: link OID to the existing user record. Refused
        # when that record already belongs to a different Azure identity; see
        # User.link_azure_identity (recycled-email account takeover).
        try:
            user.link_azure_identity(claims.oid)
        except DomainError:
            logger.warning(
                "[azure-callback] refused relink of already-linked account "
                "tid=%s email=%s incoming_oid=%s existing_oid=%s",
                claims.tid,
                _mask_email(claims.email),
                claims.oid,
                user.azure_oid,
            )
            return _error_redirect(
                "This email is already linked to a different Microsoft account. "
                "Contact your administrator."
            )

    if user.status in (UserStatus.BANNED, UserStatus.TERMINATED, UserStatus.SUSPENDED):
        return _error_redirect(f"User account is {user.status.value.lower()}. Access denied.")

    # Refresh display name from Azure on every SSO login (picks up profile renames).
    # Single save covers the first-login link above too; both mutate the same
    # entity inside one transaction.
    user.update_display_name(claims.name)
    user.record_successful_login()
    await user_repo.save(user)

    # Issue internal JWT, identical claims to password login
    refresh_jti = None
    if getattr(settings, "REFRESH_TOKEN_REVOCATION", False) and refresh_token_repo:
        refresh_jti = generate_cuid()
    token = create_token_response(
        user_id=user.id.value,
        tenant_id=tenant.id.value,
        email=user.email.value,
        refresh_jti=refresh_jti,
        role=user.role.value if user.role else None,
        access_scopes=[sc.value for sc in user.access_scopes],
    )
    if refresh_jti:
        await refresh_token_repo.save(refresh_jti, user.id.value, tenant.id.value)

    # Redirect to frontend; set cookies if cookie-mode is on
    secure = not settings.is_development
    response = RedirectResponse(
        settings.AZURE_FRONTEND_REDIRECT_URI,
        status_code=status.HTTP_302_FOUND,
    )
    if getattr(settings, "AUTH_USE_HTTPONLY_COOKIES", False):
        access_max_age = settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60
        refresh_max_age = settings.REFRESH_TOKEN_EXPIRE_DAYS * 86400
        response.set_cookie(
            key=COOKIE_ACCESS_TOKEN,
            value=token.access_token,
            max_age=access_max_age,
            path="/",
            secure=secure,
            httponly=True,
            samesite="lax",
        )
        response.set_cookie(
            key=COOKIE_REFRESH_TOKEN,
            value=token.refresh_token,
            max_age=refresh_max_age,
            path="/",
            secure=secure,
            httponly=True,
            samesite="lax",
        )
    else:
        # Bearer-token mode: embed tokens in the URL fragment so they never
        # appear in server logs or the Referer header.
        fe_url = (
            f"{settings.AZURE_FRONTEND_REDIRECT_URI}"
            f"#access_token={token.access_token}"
            f"&refresh_token={token.refresh_token}"
            f"&token_type=bearer"
            f"&expires_in={token.expires_in}"
        )
        response = RedirectResponse(fe_url, status_code=status.HTTP_302_FOUND)

    # Set after the branch: the bearer path rebinds `response`, so deleting the
    # nonce earlier would be discarded along with the original object.
    response.delete_cookie(COOKIE_SSO_STATE, path="/")
    return response
