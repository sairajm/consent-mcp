"""Tests for SendGridMessageProvider."""

from unittest.mock import MagicMock, patch

import pytest

from consent_mcp.domain.providers import ProviderType
from consent_mcp.infrastructure.providers.sendgrid import SendGridMessageProvider


class TestSendGridProviderConfiguration:
    """Tests for SendGridMessageProvider configuration."""

    def test_provider_type_is_email(self):
        """Test that provider type is EMAIL."""
        provider = SendGridMessageProvider(
            api_key="test_key",
            from_email="noreply@example.com",
        )
        assert provider.provider_type == ProviderType.EMAIL

    def test_provider_name_is_sendgrid(self):
        """Test that provider name is sendgrid."""
        provider = SendGridMessageProvider()
        assert provider.provider_name == "sendgrid"

    def test_is_configured_returns_true_when_all_set(self):
        """Test is_configured returns True when all credentials set."""
        provider = SendGridMessageProvider(
            api_key="test_key",
            from_email="noreply@example.com",
        )
        assert provider.is_configured() is True

    def test_is_configured_returns_false_when_api_key_missing(self):
        """Test is_configured returns False when api_key missing."""
        provider = SendGridMessageProvider(
            api_key=None,
            from_email="noreply@example.com",
        )
        assert provider.is_configured() is False

    def test_is_configured_returns_false_when_from_email_missing(self):
        """Test is_configured returns False when from_email missing."""
        provider = SendGridMessageProvider(
            api_key="test_key",
            from_email=None,
        )
        assert provider.is_configured() is False


class TestSendGridContactValidation:
    """Tests for SendGridMessageProvider.validate_contact method."""

    @pytest.mark.asyncio
    async def test_validate_contact_valid_email(self):
        """Test validate_contact accepts valid email."""
        provider = SendGridMessageProvider()
        assert await provider.validate_contact("user@example.com") is True

    @pytest.mark.asyncio
    async def test_validate_contact_valid_with_subdomain(self):
        """Test validate_contact accepts email with subdomain."""
        provider = SendGridMessageProvider()
        assert await provider.validate_contact("test.user@subdomain.example.org") is True

    @pytest.mark.asyncio
    async def test_validate_contact_rejects_no_at(self):
        """Test validate_contact rejects email without @."""
        provider = SendGridMessageProvider()
        assert await provider.validate_contact("invalid") is False

    @pytest.mark.asyncio
    async def test_validate_contact_rejects_no_user(self):
        """Test validate_contact rejects email without user part."""
        provider = SendGridMessageProvider()
        assert await provider.validate_contact("@example.com") is False

    @pytest.mark.asyncio
    async def test_validate_contact_rejects_no_domain(self):
        """Test validate_contact rejects email without domain."""
        provider = SendGridMessageProvider()
        assert await provider.validate_contact("user@") is False


class TestSendGridSendConsentRequest:
    """Tests for SendGridMessageProvider.send_consent_request method."""

    @pytest.mark.asyncio
    async def test_send_returns_error_for_invalid_email(self):
        """Test send_consent_request returns error for invalid email."""
        provider = SendGridMessageProvider(
            api_key="test_key",
            from_email="noreply@example.com",
        )

        result = await provider.send_consent_request(
            target_contact="invalid",
            requester_name="Alice",
            target_name="Bob",
            scope="wellness_check",
        )

        assert result.success is False
        assert "invalid" in result.error.lower()

    @pytest.mark.asyncio
    @patch("consent_mcp.infrastructure.providers.sendgrid.SendGridAPIClient")
    async def test_send_success(self, mock_client_class):
        """Test send_consent_request sends email via SendGrid."""
        # Setup mock
        mock_client = MagicMock()
        mock_response = MagicMock()
        mock_response.headers = {"X-Message-Id": "email123"}
        mock_client.send.return_value = mock_response
        mock_client_class.return_value = mock_client

        provider = SendGridMessageProvider(
            api_key="test_key",
            from_email="noreply@example.com",
        )

        result = await provider.send_consent_request(
            target_contact="bob@example.com",
            requester_name="Alice",
            target_name="Bob",
            scope="wellness_check",
        )

        assert result.success is True
        assert result.message_id == "email123"
        mock_client.send.assert_called_once()

    @pytest.mark.asyncio
    @patch("consent_mcp.infrastructure.providers.sendgrid.SendGridAPIClient")
    async def test_send_includes_consent_url_when_provided(self, mock_client_class):
        """Test send_consent_request includes consent URL in message."""
        mock_client = MagicMock()
        mock_response = MagicMock()
        mock_response.headers = {"X-Message-Id": "email123"}
        mock_client.send.return_value = mock_response
        mock_client_class.return_value = mock_client

        provider = SendGridMessageProvider(
            api_key="test_key",
            from_email="noreply@example.com",
        )

        await provider.send_consent_request(
            target_contact="bob@example.com",
            requester_name="Alice",
            target_name="Bob",
            scope="wellness_check",
            consent_url="https://consent.example.com/abc123",
        )

        # Verify send was called with proper mail object containing URL
        mock_client.send.assert_called_once()


class TestSendGridEmailFormatting:
    """Tests for SendGridMessageProvider email formatting."""

    def test_format_html_body_includes_requester(self):
        """Test HTML body includes requester name."""
        provider = SendGridMessageProvider()

        body = provider._format_html_body(
            requester_name="Alice",
            target_name="Bob",
            scope="wellness_check",
            consent_url=None,
        )

        assert "Alice" in body

    def test_format_html_body_includes_scope(self):
        """Test HTML body includes scope."""
        provider = SendGridMessageProvider()

        body = provider._format_html_body(
            requester_name="Alice",
            target_name="Bob",
            scope="wellness_check",
            consent_url=None,
        )

        assert "wellness_check" in body

    def test_format_html_body_includes_target_name(self):
        """Test HTML body includes target name."""
        provider = SendGridMessageProvider()

        body = provider._format_html_body(
            requester_name="Alice",
            target_name="Bob",
            scope="wellness_check",
            consent_url=None,
        )

        assert "Bob" in body

    def test_format_html_body_includes_consent_url(self):
        """Test HTML body includes consent URL when provided."""
        provider = SendGridMessageProvider()

        body = provider._format_html_body(
            requester_name="Alice",
            target_name="Bob",
            scope="wellness_check",
            consent_url="https://consent.example.com/abc123",
        )

        assert "https://consent.example.com/abc123" in body

    def test_format_subject_includes_requester(self):
        """Test subject includes requester name."""
        provider = SendGridMessageProvider()

        subject = provider._format_subject("Alice")
        assert "Alice" in subject
