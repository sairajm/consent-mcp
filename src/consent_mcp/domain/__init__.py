"""Domain layer for Consent MCP."""

from consent_mcp.domain.auth import AuthContext, IAuthProvider
from consent_mcp.domain.entities import ConsentRequest
from consent_mcp.domain.providers import IMessageProvider, ProviderType
from consent_mcp.domain.repository import IConsentRepository
from consent_mcp.domain.services import ConsentService
from consent_mcp.domain.value_objects import (
    ConsentStatus,
    ContactInfo,
    ContactType,
)

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
