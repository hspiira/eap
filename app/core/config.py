"""
Application Configuration

Centralized configuration management using environment variables.
All configuration values must be set via environment variables.
No defaults are provided - missing values will raise validation errors.
"""

import warnings
from pydantic import Field, field_validator, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """
    Application settings loaded from environment variables.
    
    All values are required and must be set via environment variables.
    Missing values will cause validation errors.
    """

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # Application
    APP_NAME: str = Field(description="Application name")
    APP_VERSION: str = Field(description="Application version")
    DEBUG: bool = Field(description="Debug mode")
    ENVIRONMENT: str = Field(
        description="Environment: development, staging, production"
    )

    # Database
    DATABASE_URL: str = Field(description="Database connection URL")
    DATABASE_ECHO: bool = Field(description="Echo SQL queries to console")

    # Security
    SECRET_KEY: str = Field(description="Secret key for JWT tokens")
    ALGORITHM: str = Field(description="JWT algorithm")
    ACCESS_TOKEN_EXPIRE_MINUTES: int = Field(
        description="JWT token expiration in minutes"
    )
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
    CORS_ORIGINS: str = Field(
        description="Comma-separated list of allowed CORS origins"
    )

    # Logging
    LOG_LEVEL: str = Field(
        description="Logging level: DEBUG, INFO, WARNING, ERROR, CRITICAL"
    )

    # Authorization
    STRICT_ACTIVE_USER_CHECK: bool = Field(
        default=False,
        description="If True, get_current_active_user and refresh validate user/tenant in DB",
    )
    REQUIRE_PLATFORM_ADMIN_FOR_TENANT_CREATION: bool = Field(
        default=False,
        description="If True, POST /tenants requires platform admin",
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
        default=1.0,
        description="Sampling rate for LIST/VIEW audit actions (0.0-1.0)"
    )
    
    # Comma-separated list of resource types to always audit (even for LIST/VIEW)
    # Example: "Person,Client" - these will always be logged regardless of sample rate
    AUDIT_ALWAYS_LOG_RESOURCES: str = Field(
        default="",
        description="Comma-separated resource types to always audit (e.g., 'Person,Client')"
    )
    
    # Comma-separated list of resource types to never audit for LIST/VIEW
    # Example: "AuditLog,Health" - these will never be logged for LIST/VIEW actions
    AUDIT_SKIP_RESOURCES: str = Field(
        default="",
        description="Comma-separated resource types to skip for LIST/VIEW (e.g., 'AuditLog,Health')"
    )

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
            raise ValueError(
                f"LOGIN_RATE_LIMIT_BACKEND must be one of {allowed}"
            )
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
        
        # Production-specific validations
        if self.is_production:
            if "sqlite" in self.DATABASE_URL.lower():
                warnings.warn(
                    "SQLite database is not recommended for production. "
                    "Consider using PostgreSQL or another production database.",
                    UserWarning,
                    stacklevel=2,
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
    def cors_origins_list(self) -> list[str]:
        """Get CORS origins as a list."""
        return [
            origin.strip()
            for origin in self.CORS_ORIGINS.split(",")
            if origin.strip()
        ]

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
