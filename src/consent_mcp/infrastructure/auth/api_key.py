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
        Extract API key from request.
        
        Looks for the API key in:
        1. request._meta.api_key
        2. request.params._meta.api_key (for tool calls)
        
        Args:
            request: The MCP request dictionary.
            
        Returns:
            Dict with extracted api_key if found.
        """
        # Try _meta at top level
        meta = request.get("_meta", {})
        if api_key := meta.get("api_key"):
            return {"api_key": api_key}

        # Try params._meta for tool calls
        params = request.get("params", {})
        params_meta = params.get("_meta", {})
        if api_key := params_meta.get("api_key"):
            return {"api_key": api_key}

        # Try authorization header style
        if api_key := request.get("authorization"):
            # Handle "Bearer sk_xxx" format
            if api_key.startswith("Bearer "):
                api_key = api_key[7:]
            return {"api_key": api_key}

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
            return None

        client_id = self._api_keys.get(api_key)
        if not client_id:
            return None

        return AuthContext(
            client_id=client_id,
            client_name=client_id,
            scopes=["*"],  # Full access with valid key
            metadata={"auth_method": "api_key"},
        )
