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

    # CORS
    CORS_ORIGINS: str = Field(
        description="Comma-separated list of allowed CORS origins"
    )

    # Logging
    LOG_LEVEL: str = Field(
        description="Logging level: DEBUG, INFO, WARNING, ERROR, CRITICAL"
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
        allowed = {"development", "staging", "production"}
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
