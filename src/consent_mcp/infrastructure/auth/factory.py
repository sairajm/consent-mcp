"""Auth provider factory."""

from consent_mcp.config import settings
from consent_mcp.domain.auth import AuthContext, IAuthProvider
from consent_mcp.infrastructure.auth.api_key import ApiKeyAuthProvider
from consent_mcp.infrastructure.auth.oauth import OAuthProvider


class NoAuthProvider(IAuthProvider):
    """
    No-op authentication provider for testing.

    WARNING: Only use this in test environments!
    """

    @property
    def provider_name(self) -> str:
        return "none"

    def extract_credentials(self, _request: dict) -> dict:
        return {}

    async def authenticate(self, _credentials: dict) -> AuthContext | None:
        # Always authenticate with a test context
        return AuthContext(
            client_id="test_client",
            client_name="Test Client",
            scopes=["*"],
            metadata={"auth_method": "none", "warning": "NO AUTH - TEST ONLY"},
        )


def get_auth_provider() -> IAuthProvider:
    """
    Get the configured authentication provider.

    Returns:
        The configured IAuthProvider instance.

    Raises:
        ValueError: If auth configuration is invalid.
    """
    provider_type = settings.auth_provider

    if provider_type == "none":
        if not settings.is_test_env:
            raise ValueError(
                "AUTH_PROVIDER=none is only allowed in test environment. "
                "Set ENV=test or use a different auth provider."
            )
        return NoAuthProvider()

    elif provider_type == "api_key":
        api_keys = settings.parse_api_keys()
        if not api_keys and settings.is_production:
            raise ValueError(
                "API_KEYS must be configured in production. Set API_KEYS=key1:client1,key2:client2"
            )
        return ApiKeyAuthProvider(api_keys)

    elif provider_type == "oauth":
        if not settings.oauth_issuer_url or not settings.oauth_audience:
            raise ValueError("OAuth requires OAUTH_ISSUER_URL and OAUTH_AUDIENCE to be set.")
        return OAuthProvider(
            issuer_url=settings.oauth_issuer_url,
            audience=settings.oauth_audience,
        )

    else:
        raise ValueError(f"Unknown auth provider: {provider_type}")
