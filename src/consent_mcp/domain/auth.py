"""Authentication provider interface."""

from abc import ABC, abstractmethod
from typing import Any

from pydantic import BaseModel


class AuthContext(BaseModel):
    """
    Information about an authenticated caller.
    
    This is passed to domain services for audit logging and
    authorization decisions.
    """

    client_id: str
    client_name: str | None = None
    scopes: list[str] = []
    metadata: dict[str, Any] = {}

    def has_scope(self, scope: str) -> bool:
        """Check if the client has a specific scope."""
        return scope in self.scopes or "*" in self.scopes


class IAuthProvider(ABC):
    """
    Interface for authentication providers.
    
    Implement this interface to add custom authentication mechanisms
    (e.g., API keys, OAuth, SAML, custom tokens, etc.).
    """

    @property
    @abstractmethod
    def provider_name(self) -> str:
        """Return the name of this auth provider."""
        pass

    @abstractmethod
    async def authenticate(self, credentials: dict[str, Any]) -> AuthContext | None:
        """
        Authenticate the request.
        
        Args:
            credentials: Dictionary containing authentication information
                extracted from the request.
                
        Returns:
            AuthContext if authentication succeeds, None if it fails.
        """
        pass

    @abstractmethod
    def extract_credentials(self, request: dict[str, Any]) -> dict[str, Any]:
        """
        Extract credentials from an MCP request.
        
        Args:
            request: The raw MCP request dictionary.
            
        Returns:
            Dictionary of credentials to pass to authenticate().
        """
        pass


class AuthenticationError(Exception):
    """Raised when authentication fails."""

    def __init__(self, message: str = "Authentication failed"):
        super().__init__(message)


class AuthorizationError(Exception):
    """Raised when authorization fails (authenticated but not permitted)."""

    def __init__(self, message: str = "Not authorized"):
        super().__init__(message)
