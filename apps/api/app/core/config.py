"""
Application Configuration

Centralized configuration management using environment variables.
All configuration values must be set via environment variables.
No defaults are provided - missing values will raise validation errors.
"""

import os
import warnings
from pathlib import Path

from pydantic import Field, field_validator, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

# Resolved from this file rather than the process working directory. A relative
# env_file is read from wherever the process happened to start, so running
# uvicorn from the repo root used to pick up a different .env than running it
# from apps/api.
_API_ROOT = Path(__file__).resolve().parents[2]  # apps/api
_REPO_ROOT = _API_ROOT.parents[1]  # repo root

# Tests are self-contained: apps/api/.env.test only, so a developer's local
# .env can never change what the suite sees.
if os.environ.get("ENVIRONMENT") == "test":
    _env_file: tuple[Path, ...] = (_API_ROOT / ".env.test",)
else:
    # The repo-root .env is the shared source of truth for both apps; an
    # optional apps/api/.env overrides it for backend-only tweaks. Later files
    # win, and a missing file is skipped.
    _env_file = (_REPO_ROOT / ".env", _API_ROOT / ".env")


class Settings(BaseSettings):
    """
    Application settings loaded from environment variables.

    All values are required and must be set via environment variables.
    Missing values will cause validation errors.
    """

    model_config = SettingsConfigDict(
        env_file=_env_file,
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # Application
    APP_NAME: str = Field(description="Application name")
    APP_VERSION: str = Field(description="Application version")
    DEBUG: bool = Field(description="Debug mode")
    ENVIRONMENT: str = Field(description="Environment: development, staging, production")

    # Database
    DATABASE_URL: str = Field(description="Database connection URL")
    DATABASE_ECHO: bool = Field(description="Echo SQL queries to console")

    # Security
    SECRET_KEY: str = Field(description="Secret key for JWT tokens")
    ALGORITHM: str = Field(description="JWT algorithm")
    ACCESS_TOKEN_EXPIRE_MINUTES: int = Field(description="JWT token expiration in minutes")
    REFRESH_TOKEN_EXPIRE_DAYS: int = Field(
        default=7, description="Refresh token expiration in days"
    )
    REFRESH_TOKEN_ROTATION: bool = Field(
        default=True,
        description="If True, issue new refresh token on refresh and revoke old one",
    )
    REFRESH_TOKEN_REVOCATION: bool = Field(
        default=True,
        description="If True, store refresh tokens and allow revocation (logout)",
    )
    REVOKE_PREVIOUS_REFRESH_TOKENS_ON_LOGIN: bool = Field(
        default=False,
        description="If True, revoke all existing refresh tokens for the user on successful login",
    )
    AUTH_USE_HTTPONLY_COOKIES: bool = Field(
        default=False,
        description="If True, set httpOnly cookies for access/refresh tokens and accept token from cookie or Bearer",
    )

    # CORS
    CORS_ORIGINS: str = Field(description="Comma-separated list of allowed CORS origins")

    # Logging
    LOG_LEVEL: str = Field(description="Logging level: DEBUG, INFO, WARNING, ERROR, CRITICAL")

    # Authorization
    STRICT_ACTIVE_USER_CHECK: bool = Field(
        default=True,
        description="If True, get_current_active_user and refresh validate user/tenant in DB",
    )
    REQUIRE_PLATFORM_ADMIN_FOR_TENANT_CREATION: bool = Field(
        default=True,
        description=(
            "If True, POST /tenants requires platform admin. Requires PLATFORM_TENANT_ID "
            "to be set, otherwise all tenant creation is rejected with 403 (fail-closed)."
        ),
    )
    ENFORCE_SUBSCRIPTION_LIMITS: bool = Field(
        default=False,
        description=(
            "If True, CreateClient/CreateUser use cases reject creation past "
            "the tenant's max_clients/max_users quota with a 402. When False "
            "(default), quotas are advisory only — pricing tiers are not yet "
            "wired up and we don't want to block onboarding."
        ),
    )
    # Base URL for set-password link after tenant registration (e.g. https://app.example.com or http://localhost:3000).
    # When set, tenant creation returns set_password_url instead of admin_password; user sets password then logs in.
    SET_PASSWORD_BASE_URL: str = Field(
        default="",
        description="Base URL for set-password page; when set, new tenants get set_password_url instead of admin_password",
    )
    PLATFORM_TENANT_ID: str = Field(
        default="",
        description="Tenant ID whose users are platform admins; empty means no platform admin",
    )

    # Rate limiting (always on; use higher limits in development)
    RATE_LIMIT_REQUESTS_PER_MINUTE: int = Field(
        default=60,
        description="Max requests per minute per client (production)",
    )
    RATE_LIMIT_REQUESTS_PER_HOUR: int = Field(
        default=1000,
        description="Max requests per hour per client (production)",
    )

    # Login rate limit backend: "memory" (per-process) or "redis" (shared across instances)
    LOGIN_RATE_LIMIT_BACKEND: str = Field(
        default="memory",
        description="Login rate limit backend: memory or redis",
    )
    REDIS_URL: str = Field(
        default="",
        description="Redis URL for login rate limit when LOGIN_RATE_LIMIT_BACKEND=redis",
    )

    LOGIN_LOCKOUT_THRESHOLD: int = Field(
        default=5,
        description="Consecutive failed logins before the user account is locked",
    )
    LOGIN_LOCKOUT_DURATION_MINUTES: int = Field(
        default=30,
        description="Minutes the account stays locked after threshold is reached",
    )

    ENCRYPTION_KEK: str = Field(
        default="",
        description="Base64-encoded 32-byte key-encryption key. Per-tenant DEKs are HKDF-derived from this. In production, source this from KMS.",
    )

    # Azure AD SSO (Option C: Sign in with Microsoft)
    AZURE_CLIENT_ID: str = Field(
        default="",
        description="Azure AD app registration client ID (Minet's single multi-tenant app)",
    )
    AZURE_CLIENT_SECRET: str = Field(
        default="",
        description="Azure AD app registration client secret",
    )
    AZURE_REDIRECT_URI: str = Field(
        default="",
        description="OAuth2 callback URI registered in Azure (e.g. https://api.evexia.minet.co.ug/auth/azure/callback)",
    )
    AZURE_FRONTEND_REDIRECT_URI: str = Field(
        default="",
        description="Frontend URL to redirect to after successful Azure login (e.g. https://app.evexia.minet.co.ug)",
    )

    # Security headers (middleware)
    SECURITY_HEADERS_X_FRAME_OPTIONS: str = Field(
        default="DENY",
        description="X-Frame-Options value (e.g. DENY or SAMEORIGIN)",
    )
    SECURITY_HEADERS_CSP_REPORT_ONLY: bool = Field(
        default=False,
        description="If True, set Content-Security-Policy-Report-Only with a minimal directive",
    )
    SECURITY_HEADERS_CSP_REPORT_URI: str = Field(
        default="",
        description="Report URI for CSP report-only mode (optional)",
    )

    # Document storage and URL validation
    DOCUMENT_STORAGE_PATH: str = Field(
        default="./uploads",
        description="Root directory for document file paths (path traversal checked against this)",
    )
    DOCUMENT_ALLOWED_URL_SCHEMES: str = Field(
        default="https",
        description="Comma-separated allowed URL schemes for document file_url (e.g. 'https')",
    )

    # Audit Logging
    # Sampling rate for high-volume actions (LIST, VIEW)
    # Value between 0.0 (log none) and 1.0 (log all)
    # Default: 1.0 (log all) - set to lower value (e.g., 0.1 for 10%) to reduce volume
    AUDIT_SAMPLE_RATE: float = Field(
        default=1.0, description="Sampling rate for LIST/VIEW audit actions (0.0-1.0)"
    )

    # Comma-separated list of resource types to always audit (even for LIST/VIEW)
    # Example: "Person,Client" - these will always be logged regardless of sample rate
    AUDIT_ALWAYS_LOG_RESOURCES: str = Field(
        default="",
        description="Comma-separated resource types to always audit (e.g., 'Person,Client')",
    )

    # Comma-separated list of resource types to never audit for LIST/VIEW
    # Example: "AuditLog,Health" - these will never be logged for LIST/VIEW actions
    AUDIT_SKIP_RESOURCES: str = Field(
        default="",
        description="Comma-separated resource types to skip for LIST/VIEW (e.g., 'AuditLog,Health')",
    )

    @field_validator("DATABASE_URL")
    @classmethod
    def normalize_database_url(cls, v: str) -> str:
        """Ensure asyncpg driver and ssl=require for PostgreSQL URLs (Neon integration compat)."""
        if v.startswith("postgres://") or v.startswith("postgresql://"):
            v = v.replace("postgres://", "postgresql+asyncpg://", 1).replace(
                "postgresql://", "postgresql+asyncpg://", 1
            )
        # Replace legacy ssl params Neon sometimes injects
        for old in ("sslmode=require", "channel_binding=require"):
            v = v.replace(old, "ssl=require")
        # Deduplicate ssl=require if both were present
        while "ssl=require&ssl=require" in v:
            v = v.replace("ssl=require&ssl=require", "ssl=require")
        return v

    @field_validator("ENVIRONMENT")
    @classmethod
    def validate_environment(cls, v: str) -> str:
        """Validate environment value."""
        allowed = {"development", "staging", "production", "test"}
        if v.lower() not in allowed:
            raise ValueError(f"ENVIRONMENT must be one of {allowed}")
        return v.lower()

    @field_validator("LOG_LEVEL")
    @classmethod
    def validate_log_level(cls, v: str) -> str:
        """Validate log level."""
        allowed = {"DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"}
        if v.upper() not in allowed:
            raise ValueError(f"LOG_LEVEL must be one of {allowed}")
        return v.upper()

    @field_validator("LOGIN_RATE_LIMIT_BACKEND")
    @classmethod
    def validate_login_rate_limit_backend(cls, v: str) -> str:
        """Validate login rate limit backend."""
        allowed = {"memory", "redis"}
        if v.lower() not in allowed:
            raise ValueError(f"LOGIN_RATE_LIMIT_BACKEND must be one of {allowed}")
        return v.lower()

    @field_validator("AUDIT_SAMPLE_RATE")
    @classmethod
    def validate_audit_sample_rate(cls, v: float) -> float:
        """Validate audit sample rate."""
        if not 0.0 <= v <= 1.0:
            raise ValueError("AUDIT_SAMPLE_RATE must be between 0.0 and 1.0")
        return v

    @model_validator(mode="after")
    def validate_config(self) -> "Settings":
        """Validate configuration and warn about missing or invalid values."""
        missing = []

        # Check for empty strings (which might indicate missing env vars)
        if not self.SECRET_KEY or self.SECRET_KEY.strip() == "":
            missing.append("SECRET_KEY")
        if not self.DATABASE_URL or self.DATABASE_URL.strip() == "":
            missing.append("DATABASE_URL")

        if missing:
            raise ValueError(
                f"Missing required configuration: {', '.join(missing)}. "
                "Set these via environment variables."
            )

        if self.LOGIN_RATE_LIMIT_BACKEND == "redis" and not (self.REDIS_URL or "").strip():
            warnings.warn(
                "LOGIN_RATE_LIMIT_BACKEND is 'redis' but REDIS_URL is empty. "
                "Falling back to memory backend.",
                UserWarning,
                stacklevel=2,
            )

        return self

    @property
    def azure_sso_configured(self) -> bool:
        """True when all four Azure SSO env vars are present."""
        return bool(
            self.AZURE_CLIENT_ID
            and self.AZURE_CLIENT_SECRET
            and self.AZURE_REDIRECT_URI
            and self.AZURE_FRONTEND_REDIRECT_URI
        )

    @property
    def cors_origins_list(self) -> list[str]:
        """Get CORS origins as a list."""
        return [origin.strip() for origin in self.CORS_ORIGINS.split(",") if origin.strip()]

    @property
    def is_development(self) -> bool:
        """Check if running in development environment."""
        return self.ENVIRONMENT == "development"

    @property
    def is_production(self) -> bool:
        """Check if running in production environment."""
        return self.ENVIRONMENT == "production"

    @property
    def audit_always_log_resources_list(self) -> list[str]:
        """Get always-log resource types as a list."""
        if not self.AUDIT_ALWAYS_LOG_RESOURCES:
            return []
        return [
            resource.strip()
            for resource in self.AUDIT_ALWAYS_LOG_RESOURCES.split(",")
            if resource.strip()
        ]

    @property
    def audit_skip_resources_list(self) -> list[str]:
        """Get skip resource types as a list."""
        if not self.AUDIT_SKIP_RESOURCES:
            return []
        return [
            resource.strip()
            for resource in self.AUDIT_SKIP_RESOURCES.split(",")
            if resource.strip()
        ]


# Global settings instance
settings = Settings()
