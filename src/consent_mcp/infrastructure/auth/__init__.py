"""Authentication providers for the MCP server."""

from consent_mcp.infrastructure.auth.api_key import ApiKeyAuthProvider
from consent_mcp.infrastructure.auth.oauth import OAuthProvider
from consent_mcp.infrastructure.auth.factory import get_auth_provider

__all__ = [
    "ApiKeyAuthProvider",
    "OAuthProvider",
    "get_auth_provider",
]
