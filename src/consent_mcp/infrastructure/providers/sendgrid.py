"""SendGrid email provider implementation."""

import re

from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail
from python_http_client.exceptions import HTTPError

from consent_mcp.config import settings
from consent_mcp.domain.providers import (
    IMessageProvider,
    MessageDeliveryResult,
    ProviderNotConfiguredError,
    ProviderType,
)


# Simple email validation pattern
EMAIL_PATTERN = re.compile(r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$")


class SendGridMessageProvider(IMessageProvider):
    """SendGrid email implementation of the message provider."""

    def __init__(
        self,
        api_key: str | None = None,
        from_email: str | None = None,
    ):
        """
        Initialize the SendGrid provider.
        
        Args:
            api_key: SendGrid API key. Defaults to settings.
            from_email: Sender email address. Defaults to settings.
        """
        self._api_key = api_key or settings.sendgrid_api_key
        self._from_email = from_email or settings.sendgrid_from_email
        self._client: SendGridAPIClient | None = None

    @property
    def provider_type(self) -> ProviderType:
        """Return EMAIL provider type."""
        return ProviderType.EMAIL

    @property
    def provider_name(self) -> str:
        """Return provider name."""
        return "sendgrid"

    def is_configured(self) -> bool:
        """Check if SendGrid is properly configured."""
        return all([
            self._api_key,
            self._from_email,
        ])

    def _get_client(self) -> SendGridAPIClient:
        """Get or create the SendGrid client."""
        if not self.is_configured():
            raise ProviderNotConfiguredError(
                "SendGrid is not configured. Set SENDGRID_API_KEY "
                "and SENDGRID_FROM_EMAIL."
            )
        if self._client is None:
            self._client = SendGridAPIClient(self._api_key)
        return self._client

    async def validate_contact(self, contact_value: str) -> bool:
        """Validate email address format."""
        return bool(EMAIL_PATTERN.match(contact_value))

    def _format_subject(self, requester_name: str) -> str:
        """Format the email subject."""
        return f"Consent Request from {requester_name}"

    def _format_html_body(
        self,
        requester_name: str,
        target_name: str | None,
        scope: str,
        consent_url: str | None,
    ) -> str:
        """Format the consent request email body (HTML)."""
        greeting = f"Hi {target_name}" if target_name else "Hello"
        
        button_html = ""
        if consent_url:
            button_html = f"""
            <p style="margin-top: 20px;">
                <a href="{consent_url}" 
                   style="background-color: #4CAF50; color: white; padding: 14px 20px; 
                          text-decoration: none; border-radius: 4px;">
                    Grant Consent
                </a>
            </p>
            """
        else:
            button_html = """
            <p style="margin-top: 20px; color: #666;">
                Reply to this email with <strong>YES</strong> to grant consent 
                or <strong>NO</strong> to decline.
            </p>
            """

        return f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="utf-8">
        </head>
        <body style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
            <div style="padding: 20px; background-color: #f9f9f9; border-radius: 8px;">
                <h2 style="color: #333;">AI Agent Consent Request</h2>
                <p>{greeting},</p>
                <p><strong>{requester_name}</strong> is requesting permission for an AI agent 
                   to contact you for the following purpose:</p>
                <blockquote style="background-color: #fff; padding: 15px; 
                                   border-left: 4px solid #4CAF50; margin: 20px 0;">
                    {scope}
                </blockquote>
                {button_html}
                <hr style="margin-top: 30px; border: none; border-top: 1px solid #ddd;">
                <p style="color: #999; font-size: 12px;">
                    This is an automated consent request. If you did not expect this email,
                    you can safely ignore it.
                </p>
            </div>
        </body>
        </html>
        """

    def _format_plain_body(
        self,
        requester_name: str,
        target_name: str | None,
        scope: str,
    ) -> str:
        """Format the consent request email body (plain text)."""
        greeting = f"Hi {target_name}" if target_name else "Hello"
        return (
            f"{greeting},\n\n"
            f"{requester_name} is requesting permission for an AI agent "
            f"to contact you for: {scope}\n\n"
            f"Reply YES to grant consent or NO to decline.\n\n"
            f"---\n"
            f"This is an automated consent request."
        )

    async def send_consent_request(
        self,
        target_contact: str,
        requester_name: str,
        target_name: str | None,
        scope: str,
        consent_url: str | None = None,
    ) -> MessageDeliveryResult:
        """Send a consent request via email."""
        if not await self.validate_contact(target_contact):
            return MessageDeliveryResult(
                success=False,
                provider=self.provider_name,
                error=f"Invalid email address: {target_contact}",
            )

        message = Mail(
            from_email=self._from_email,
            to_emails=target_contact,
            subject=self._format_subject(requester_name),
            html_content=self._format_html_body(
                requester_name, target_name, scope, consent_url
            ),
            plain_text_content=self._format_plain_body(
                requester_name, target_name, scope
            ),
        )

        try:
            client = self._get_client()
            response = client.send(message)
            
            # Extract message ID from response headers
            message_id = response.headers.get("X-Message-Id", None)
            
            return MessageDeliveryResult(
                success=True,
                provider=self.provider_name,
                message_id=message_id,
            )
        except HTTPError as e:
            return MessageDeliveryResult(
                success=False,
                provider=self.provider_name,
                error=f"SendGrid error: {e.body}",
            )
        except Exception as e:
            return MessageDeliveryResult(
                success=False,
                provider=self.provider_name,
                error=f"Unexpected error: {str(e)}",
            )
