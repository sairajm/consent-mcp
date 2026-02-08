"""Twilio SMS provider implementation."""

import re

from twilio.base.exceptions import TwilioRestException
from twilio.rest import Client

from consent_mcp.config import settings
from consent_mcp.domain.providers import (
    IMessageProvider,
    MessageDeliveryResult,
    ProviderNotConfiguredError,
    ProviderType,
)

# E.164 phone number pattern
E164_PATTERN = re.compile(r"^\+[1-9]\d{1,14}$")


# Sentinel for unset values
_UNSET = object()


class TwilioMessageProvider(IMessageProvider):
    """Twilio SMS implementation of the message provider."""

    def __init__(
        self,
        account_sid: str | None = _UNSET,
        auth_token: str | None = _UNSET,
        phone_number: str | None = _UNSET,
    ):
        """
        Initialize the Twilio provider.

        Args:
            account_sid: Twilio Account SID. Defaults to settings.
            auth_token: Twilio Auth Token. Defaults to settings.
            phone_number: Twilio phone number for sending. Defaults to settings.
        """
        self._account_sid = (
            account_sid if account_sid is not _UNSET else settings.twilio_account_sid
        )
        self._auth_token = auth_token if auth_token is not _UNSET else settings.twilio_auth_token
        self._phone_number = (
            phone_number if phone_number is not _UNSET else settings.twilio_phone_number
        )
        self._client: Client | None = None

    @property
    def provider_type(self) -> ProviderType:
        """Return SMS provider type."""
        return ProviderType.SMS

    @property
    def provider_name(self) -> str:
        """Return provider name."""
        return "twilio"

    def is_configured(self) -> bool:
        """Check if Twilio is properly configured."""
        return all(
            [
                self._account_sid,
                self._auth_token,
                self._phone_number,
            ]
        )

    def _get_client(self) -> Client:
        """Get or create the Twilio client."""
        if not self.is_configured():
            raise ProviderNotConfiguredError(
                "Twilio is not configured. Set TWILIO_ACCOUNT_SID, "
                "TWILIO_AUTH_TOKEN, and TWILIO_PHONE_NUMBER."
            )
        if self._client is None:
            self._client = Client(self._account_sid, self._auth_token)
        return self._client

    async def validate_contact(self, contact_value: str) -> bool:
        """Validate phone number format."""
        return bool(E164_PATTERN.match(contact_value))

    def _format_message(
        self,
        requester_name: str,
        target_name: str | None,
        scope: str,
        consent_url: str | None = None,
    ) -> str:
        """Format the consent request SMS message."""
        greeting = f"Hi {target_name}" if target_name else "Hi"

        if consent_url:
            return (
                f"{greeting}, {requester_name} requests AI agent consent for: {scope}. "
                f"Click to grant consent: {consent_url}"
            )
        else:
            return (
                f"{greeting}, {requester_name} is requesting AI agent consent for: {scope}. "
                f"Reply YES to grant or NO to decline."
            )

    async def send_consent_request(
        self,
        target_contact: str,
        requester_name: str,
        target_name: str | None,
        scope: str,
        consent_url: str | None = None,
    ) -> MessageDeliveryResult:
        """Send a consent request via SMS."""
        if not await self.validate_contact(target_contact):
            return MessageDeliveryResult(
                success=False,
                provider=self.provider_name,
                error=f"Invalid phone number format: {target_contact}",
            )

        message_body = self._format_message(requester_name, target_name, scope, consent_url)

        try:
            client = self._get_client()
            message = client.messages.create(
                body=message_body,
                from_=self._phone_number,
                to=target_contact,
            )
            return MessageDeliveryResult(
                success=True,
                provider=self.provider_name,
                message_id=message.sid,
            )
        except TwilioRestException as e:
            return MessageDeliveryResult(
                success=False,
                provider=self.provider_name,
                error=f"Twilio error: {e.msg}",
            )
        except Exception as e:
            return MessageDeliveryResult(
                success=False,
                provider=self.provider_name,
                error=f"Unexpected error: {str(e)}",
            )
