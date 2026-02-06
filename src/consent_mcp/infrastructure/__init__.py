"""Infrastructure layer for Consent MCP."""

from consent_mcp.infrastructure.database import (
    get_async_session,
    init_db,
    PostgresConsentRepository,
)
from consent_mcp.infrastructure.providers import (
    TwilioMessageProvider,
    SendGridMessageProvider,
    get_sms_provider,
    get_email_provider,
)
from consent_mcp.infrastructure.auth import (
    ApiKeyAuthProvider,
    OAuthProvider,
    get_auth_provider,
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
