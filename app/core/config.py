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


# Global settings instance
settings = Settings()
