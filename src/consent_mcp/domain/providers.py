"""Message provider interface for sending consent requests."""

from abc import ABC, abstractmethod
from enum import Enum

from pydantic import BaseModel


class ProviderType(str, Enum):
    """Type of message provider."""

    SMS = "sms"
    EMAIL = "email"


class MessageDeliveryResult(BaseModel):
    """Result of attempting to send a message."""

    success: bool
    provider: str
    message_id: str | None = None
    error: str | None = None


class IMessageProvider(ABC):
    """
    Interface for sending consent request messages.
    
    Implement this interface to add new messaging providers
    (e.g., WhatsApp, push notifications, etc.).
    """

    @property
    @abstractmethod
    def provider_type(self) -> ProviderType:
        """Return the type of provider (SMS or EMAIL)."""
        pass

    @property
    @abstractmethod
    def provider_name(self) -> str:
        """Return the name of the provider (e.g., 'twilio', 'sendgrid')."""
        pass

    @abstractmethod
    async def send_consent_request(
        self,
        target_contact: str,
        requester_name: str,
        target_name: str | None,
        scope: str,
        consent_url: str | None = None,
    ) -> MessageDeliveryResult:
        """
        Send a consent request message to the target.
        
        Args:
            target_contact: Phone number or email address of target.
            requester_name: Display name of the requester.
            target_name: Display name of the target (if known).
            scope: Description of what consent is for.
            consent_url: Optional URL for target to click to grant consent.
            
        Returns:
            MessageDeliveryResult with success status and details.
        """
        pass

    @abstractmethod
    async def validate_contact(self, contact_value: str) -> bool:
        """
        Validate the contact format.
        
        Args:
            contact_value: Phone number or email to validate.
            
        Returns:
            True if valid, False otherwise.
        """
        pass

    @abstractmethod
    def is_configured(self) -> bool:
        """
        Check if the provider is properly configured.
        
        Returns:
            True if all required credentials are set.
        """
        pass


class ProviderError(Exception):
    """Base exception for provider errors."""

    pass


class ProviderNotConfiguredError(ProviderError):
    """Raised when trying to use an unconfigured provider."""

    pass


class MessageDeliveryError(ProviderError):
    """Raised when message delivery fails."""

    def __init__(self, message: str, provider: str, details: dict | None = None):
        super().__init__(message)
        self.provider = provider
        self.details = details or {}
