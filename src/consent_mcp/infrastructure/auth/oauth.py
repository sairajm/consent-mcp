"""OAuth/JWT authentication provider."""

from typing import Any

import httpx
from jose import JWTError, jwt
from jose.exceptions import JWTClaimsError

from consent_mcp.domain.auth import AuthContext, IAuthProvider


class OAuthProvider(IAuthProvider):
    """
    OAuth 2.0 / JWT token authentication.

    Validates JWT tokens against a configured issuer using JWKS.
    """

    def __init__(
        self,
        issuer_url: str,
        audience: str,
        algorithms: list[str] | None = None,
    ):
        """
        Initialize the OAuth provider.

        Args:
            issuer_url: The OAuth issuer URL (e.g., https://auth.example.com).
            audience: Expected audience claim in the JWT.
            algorithms: Allowed signing algorithms. Defaults to RS256.
        """
        self._issuer_url = issuer_url.rstrip("/")
        self._audience = audience
        self._algorithms = algorithms or ["RS256"]
        self._jwks: dict | None = None

    @property
    def provider_name(self) -> str:
        """Return provider name."""
        return "oauth"

    async def _fetch_jwks(self) -> dict:
        """Fetch JWKS from the issuer."""
        if self._jwks is not None:
            return self._jwks

        jwks_url = f"{self._issuer_url}/.well-known/jwks.json"
        async with httpx.AsyncClient() as client:
            response = await client.get(jwks_url)
            response.raise_for_status()
            self._jwks = response.json()
        return self._jwks

    def extract_credentials(self, request: dict[str, Any]) -> dict[str, Any]:
        """
        Extract bearer token from request.

        Looks for:
        1. request.authorization header
        2. request._meta.bearer_token

        Args:
            request: The MCP request dictionary.

        Returns:
            Dict with extracted bearer_token if found.
        """
        # Check authorization header
        if auth := request.get("authorization"):
            if auth.startswith("Bearer "):
                return {"bearer_token": auth[7:]}
            return {"bearer_token": auth}

        # Check _meta
        meta = request.get("_meta", {})
        if token := meta.get("bearer_token"):
            return {"bearer_token": token}

        # Check params._meta for tool calls
        params = request.get("params", {})
        params_meta = params.get("_meta", {})
        if token := params_meta.get("bearer_token"):
            return {"bearer_token": token}

        return {}

    async def authenticate(self, credentials: dict[str, Any]) -> AuthContext | None:
        """
        Authenticate using JWT token.

        Args:
            credentials: Dict containing 'bearer_token'.

        Returns:
            AuthContext if valid token, None otherwise.
        """
        token = credentials.get("bearer_token")
        if not token:
            return None

        try:
            # Fetch JWKS for verification
            jwks = await self._fetch_jwks()

            # Decode and verify the token
            # Note: In production, you'd want to cache the signing key
            unverified_header = jwt.get_unverified_header(token)

            # Find the matching key
            rsa_key = None
            for key in jwks.get("keys", []):
                if key.get("kid") == unverified_header.get("kid"):
                    rsa_key = key
                    break

            if not rsa_key:
                return None

            # Verify the token
            payload = jwt.decode(
                token,
                rsa_key,
                algorithms=self._algorithms,
                audience=self._audience,
                issuer=self._issuer_url,
            )

            # Extract claims
            subject = payload.get("sub", "unknown")
            scopes = payload.get("scope", "").split() if payload.get("scope") else []

            return AuthContext(
                client_id=subject,
                client_name=payload.get("name"),
                scopes=scopes,
                metadata={
                    "auth_method": "oauth",
                    "issuer": self._issuer_url,
                },
            )

        except (JWTError, JWTClaimsError, httpx.HTTPError):
            # Log the error in production
            return None
