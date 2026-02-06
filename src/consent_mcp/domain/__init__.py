"""Domain layer for Consent MCP."""

from consent_mcp.domain.entities import ConsentRequest
from consent_mcp.domain.value_objects import (
    ContactInfo,
    ContactType,
    ConsentStatus,
)
from consent_mcp.domain.repository import IConsentRepository
from consent_mcp.domain.providers import IMessageProvider, ProviderType
from consent_mcp.domain.auth import IAuthProvider, AuthContext
from consent_mcp.domain.services import ConsentService

__all__ = [
    "ConsentRequest",
    "ContactInfo",
    "ContactType",
    "ConsentStatus",
    "IConsentRepository",
    "IMessageProvider",
    "ProviderType",
    "IAuthProvider",
    "AuthContext",
    "ConsentService",
]
