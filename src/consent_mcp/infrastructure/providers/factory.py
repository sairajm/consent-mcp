"""Provider factory for creating messaging providers."""

from consent_mcp.config import settings
from consent_mcp.domain.providers import IMessageProvider
from consent_mcp.infrastructure.providers.sendgrid import SendGridMessageProvider
from consent_mcp.infrastructure.providers.twilio import TwilioMessageProvider


def get_sms_provider() -> IMessageProvider | None:
    """
    Get the configured SMS provider.

    Returns:
        TwilioMessageProvider if configured, None otherwise.
    """
    if settings.twilio_configured:
        return TwilioMessageProvider()
    return None


def get_email_provider() -> IMessageProvider | None:
    """
    Get the configured email provider.

    Returns:
        SendGridMessageProvider if configured, None otherwise.
    """
    if settings.sendgrid_configured:
        return SendGridMessageProvider()
    return None
