"""
Application configuration using Pydantic settings.
"""
from typing import List, Optional
from pydantic_settings import BaseSettings
from pydantic import Field, field_validator
from functools import lru_cache


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    # Application
    APP_NAME: str = "Vividly API"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = False
    ENVIRONMENT: str = "development"

    # Server
    HOST: str = "0.0.0.0"
    PORT: int = 8000

    # Database
    DATABASE_URL: str = Field(..., description="PostgreSQL connection string")
    DATABASE_CONNECTION_NAME: Optional[str] = None
    DATABASE_USER: Optional[str] = None
    DATABASE_PASSWORD: Optional[str] = None
    DATABASE_NAME: Optional[str] = None

    # JWT Authentication
    SECRET_KEY: str = Field(..., description="Secret key for JWT signing")
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 1440  # 24 hours
    REFRESH_TOKEN_EXPIRE_DAYS: int = 30

    # Email
    SMTP_HOST: str = "smtp.gmail.com"
    SMTP_PORT: int = 587
    SMTP_USER: Optional[str] = None
    SMTP_PASSWORD: Optional[str] = None
    FROM_EMAIL: str = "noreply@vividly.com"
    FROM_NAME: str = "Vividly"

    # Google Cloud
    GCP_PROJECT_ID: str = "vividly-dev-rich"
    GCS_BUCKET_OER: str = "vividly-dev-rich-dev-oer-content"
    GCS_BUCKET_GENERATED: str = "vividly-dev-rich-dev-generated-content"
    GCS_BUCKET_TEMP: str = "vividly-dev-rich-dev-temp-files"

    # Rate Limiting
    RATE_LIMIT_LOGIN: str = "5/15minute"
    RATE_LIMIT_REGISTER: str = "3/hour"
    RATE_LIMIT_PASSWORD_RESET: str = "3/hour"

    # CORS
    CORS_ORIGINS: List[str] = ["http://localhost:3000", "http://localhost:8080"]
    CORS_ALLOW_CREDENTIALS: bool = True
    CORS_ALLOW_METHODS: List[str] = ["*"]
    CORS_ALLOW_HEADERS: List[str] = ["*"]

    # Logging
    LOG_LEVEL: str = "INFO"

    @field_validator("CORS_ORIGINS", mode="before")
    @classmethod
    def parse_cors_origins(cls, v):
        """Parse CORS origins from comma-separated string if needed."""
        if isinstance(v, str):
            return [origin.strip() for origin in v.split(",")]
        return v

    class Config:
        env_file = ".env"
        case_sensitive = True


# Global settings instance
settings = Settings()


@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance."""
    return settings
