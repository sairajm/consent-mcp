"""Infrastructure layer for Consent MCP."""

from consent_mcp.infrastructure.auth import (
    ApiKeyAuthProvider,
    OAuthProvider,
    get_auth_provider,
)
from consent_mcp.infrastructure.database import (
    PostgresConsentRepository,
    get_async_session,
    init_db,
)
from consent_mcp.infrastructure.providers import (
    SendGridMessageProvider,
    TwilioMessageProvider,
    get_email_provider,
    get_sms_provider,
)

__all__ = [
    # Database
    "get_async_session",
    "init_db",
    "PostgresConsentRepository",
    # Providers
    "TwilioMessageProvider",
    "SendGridMessageProvider",
    "get_sms_provider",
    "get_email_provider",
    # Auth
    "ApiKeyAuthProvider",
    "OAuthProvider",
    "get_auth_provider",
]
