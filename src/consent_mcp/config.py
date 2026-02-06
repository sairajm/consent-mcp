"""Configuration management for Consent MCP."""

from functools import lru_cache
from typing import Literal

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # Environment
    env: Literal["test", "development", "production"] = Field(
        default="development",
        description="Application environment",
    )

    # Database
    database_url: str = Field(
        default="postgresql+asyncpg://consent:consent@localhost:5432/consent_db",
        description="PostgreSQL connection URL",
    )

    # Authentication
    auth_provider: Literal["api_key", "oauth", "none"] = Field(
        default="api_key",
        description="Authentication provider to use",
    )
    api_keys: str = Field(
        default="",
        description="Comma-separated API key:client_id pairs",
    )
    oauth_issuer_url: str | None = Field(
        default=None,
        description="OAuth issuer URL for JWT validation",
    )
    oauth_audience: str | None = Field(
        default=None,
        description="OAuth audience for JWT validation",
    )

    # Twilio SMS Provider
    twilio_account_sid: str | None = Field(
        default=None,
        description="Twilio Account SID",
    )
    twilio_auth_token: str | None = Field(
        default=None,
        description="Twilio Auth Token",
    )
    twilio_phone_number: str | None = Field(
        default=None,
        description="Twilio phone number for sending SMS",
    )

    # SendGrid Email Provider
    sendgrid_api_key: str | None = Field(
        default=None,
        description="SendGrid API key",
    )
    sendgrid_from_email: str | None = Field(
        default=None,
        description="SendGrid sender email address",
    )

    @field_validator("auth_provider")
    @classmethod
    def validate_auth_provider(cls, v: str, info) -> str:
        """Ensure 'none' auth is only used in test environment."""
        # Note: We can't access other fields in field_validator easily,
        # so we do runtime check in the auth factory
        return v

    def parse_api_keys(self) -> dict[str, str]:
        """Parse API keys from comma-separated string to dict."""
        if not self.api_keys:
            return {}
        result = {}
        for pair in self.api_keys.split(","):
            pair = pair.strip()
            if ":" in pair:
                key, client_id = pair.split(":", 1)
                result[key.strip()] = client_id.strip()
        return result

    @property
    def is_test_env(self) -> bool:
        """Check if running in test environment."""
        return self.env == "test"

    @property
    def is_production(self) -> bool:
        """Check if running in production environment."""
        return self.env == "production"

    @property
    def twilio_configured(self) -> bool:
        """Check if Twilio is fully configured."""
        return all([
            self.twilio_account_sid,
            self.twilio_auth_token,
            self.twilio_phone_number,
        ])

    @property
    def sendgrid_configured(self) -> bool:
        """Check if SendGrid is fully configured."""
        return all([
            self.sendgrid_api_key,
            self.sendgrid_from_email,
        ])


@lru_cache
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()


# Convenience accessor
settings = get_settings()
