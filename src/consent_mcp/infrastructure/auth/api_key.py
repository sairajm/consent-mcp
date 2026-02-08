"""API Key authentication provider."""

from typing import Any

from consent_mcp.domain.auth import AuthContext, IAuthProvider


class ApiKeyAuthProvider(IAuthProvider):
    """
    Simple API key authentication.

    Keys are mapped to client IDs. Each key authenticates as a specific client.
    """

    def __init__(self, api_keys: dict[str, str]):
        """
        Initialize with API keys.

        Args:
            api_keys: Mapping of API key -> client_id.
        """
        self._api_keys = api_keys

    @property
    def provider_name(self) -> str:
        """Return provider name."""
        return "api_key"

    def extract_credentials(self, request: dict[str, Any]) -> dict[str, Any]:
        """
        Extract credentials from the request.

        Supports multiple sources:
        1. HTTP Authorization header (Bearer token) - for SSE/HTTP transport
        2. MCP_BOOTSTRAP_KEY environment variable - for session-level auth
        3. Legacy _meta.api_key - for backward compatibility

        Args:
            request: Request dictionary containing headers or metadata

        Returns:
            Dictionary with extracted credentials
        """
        # Priority 1: HTTP Authorization header (SSE/HTTP transport)
        if auth_header := request.get("authorization", ""):
            # Extract Bearer token
            if auth_header.lower().startswith("bearer "):
                api_key = auth_header[7:].strip()  # Remove "bearer " prefix
                return {"api_key": api_key}

        # Priority 2: Legacy _meta field
        if "_meta" in request:
            params = request.get("_meta", {})
            if api_key := params.get("api_key"):
                return {"api_key": api_key}

        # Priority 3: Bootstrap key from environment (for backward compatibility)
        import os

        if bootstrap_key := os.environ.get("MCP_BOOTSTRAP_KEY"):
            return {"api_key": bootstrap_key}

        return {}

    async def authenticate(self, credentials: dict[str, Any]) -> AuthContext | None:
        """
        Authenticate using API key.

        Args:
            credentials: Dict containing 'api_key'.

        Returns:
            AuthContext if valid key, None otherwise.
        """
        api_key = credentials.get("api_key")

        if not api_key:
            return

        client_id = self._api_keys.get(api_key)

        if not client_id:
            return None

        return AuthContext(
            client_id=client_id,
            client_name=client_id,
            scopes=["*"],  # Full access with valid key
            metadata={"auth_method": "api_key"},
        )
