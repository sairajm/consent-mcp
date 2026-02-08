"""Tests for TwilioMessageProvider."""

from unittest.mock import MagicMock, patch

import pytest

from consent_mcp.domain.providers import ProviderType
from consent_mcp.infrastructure.providers.twilio import TwilioMessageProvider


class TestTwilioProviderConfiguration:
    """Tests for TwilioMessageProvider configuration."""

    def test_provider_type_is_sms(self):
        """Test that provider type is SMS."""
        provider = TwilioMessageProvider(
            account_sid="test_sid",
            auth_token="test_token",
            phone_number="+15551234567",
        )
        assert provider.provider_type == ProviderType.SMS

    def test_provider_name_is_twilio(self):
        """Test that provider name is twilio."""
        provider = TwilioMessageProvider()
        assert provider.provider_name == "twilio"

    def test_is_configured_returns_true_when_all_set(self):
        """Test is_configured returns True when all credentials set."""
        provider = TwilioMessageProvider(
            account_sid="test_sid",
            auth_token="test_token",
            phone_number="+15551234567",
        )
        assert provider.is_configured() is True

    def test_is_configured_returns_false_when_account_sid_missing(self):
        """Test is_configured returns False when account_sid missing."""
        provider = TwilioMessageProvider(
            account_sid=None,
            auth_token="test_token",
            phone_number="+15551234567",
        )
        assert provider.is_configured() is False

    def test_is_configured_returns_false_when_auth_token_missing(self):
        """Test is_configured returns False when auth_token missing."""
        provider = TwilioMessageProvider(
            account_sid="test_sid",
            auth_token=None,
            phone_number="+15551234567",
        )
        assert provider.is_configured() is False

    def test_is_configured_returns_false_when_phone_missing(self):
        """Test is_configured returns False when phone_number missing."""
        provider = TwilioMessageProvider(
            account_sid="test_sid",
            auth_token="test_token",
            phone_number=None,
        )
        assert provider.is_configured() is False


class TestTwilioContactValidation:
    """Tests for TwilioMessageProvider.validate_contact method."""

    @pytest.mark.asyncio
    async def test_validate_contact_valid_e164_phone(self):
        """Test validate_contact accepts valid E.164 phone."""
        provider = TwilioMessageProvider()
        assert await provider.validate_contact("+15551234567") is True

    @pytest.mark.asyncio
    async def test_validate_contact_valid_international_phone(self):
        """Test validate_contact accepts valid international phone."""
        provider = TwilioMessageProvider()
        assert await provider.validate_contact("+447911123456") is True

    @pytest.mark.asyncio
    async def test_validate_contact_rejects_no_plus(self):
        """Test validate_contact rejects phone without + prefix."""
        provider = TwilioMessageProvider()
        assert await provider.validate_contact("5551234567") is False

    @pytest.mark.asyncio
    async def test_validate_contact_rejects_too_short(self):
        """Test validate_contact rejects too short phone."""
        provider = TwilioMessageProvider()
        assert await provider.validate_contact("+1") is False

    @pytest.mark.asyncio
    async def test_validate_contact_rejects_invalid_chars(self):
        """Test validate_contact rejects invalid characters."""
        provider = TwilioMessageProvider()
        assert await provider.validate_contact("invalid") is False
        assert await provider.validate_contact("+1555CALL") is False


class TestTwilioSendConsentRequest:
    """Tests for TwilioMessageProvider.send_consent_request method."""

    @pytest.mark.asyncio
    async def test_send_returns_error_for_invalid_phone(self):
        """Test send_consent_request returns error for invalid phone."""
        provider = TwilioMessageProvider(
            account_sid="test_sid",
            auth_token="test_token",
            phone_number="+15551234567",
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
    @patch("consent_mcp.infrastructure.providers.twilio.Client")
    async def test_send_success(self, mock_client_class):
        """Test send_consent_request sends SMS via Twilio."""
        # Setup mock
        mock_client = MagicMock()
        mock_message = MagicMock()
        mock_message.sid = "SM123456"
        mock_client.messages.create.return_value = mock_message
        mock_client_class.return_value = mock_client

        provider = TwilioMessageProvider(
            account_sid="test_sid",
            auth_token="test_token",
            phone_number="+15551234567",
        )

        result = await provider.send_consent_request(
            target_contact="+15559876543",
            requester_name="Alice",
            target_name="Bob",
            scope="wellness_check",
        )

        assert result.success is True
        assert result.message_id == "SM123456"
        mock_client.messages.create.assert_called_once()

    @pytest.mark.asyncio
    @patch("consent_mcp.infrastructure.providers.twilio.Client")
    async def test_send_includes_consent_url_when_provided(self, mock_client_class):
        """Test send_consent_request includes consent URL in message."""
        mock_client = MagicMock()
        mock_message = MagicMock()
        mock_message.sid = "SM123456"
        mock_client.messages.create.return_value = mock_message
        mock_client_class.return_value = mock_client

        provider = TwilioMessageProvider(
            account_sid="test_sid",
            auth_token="test_token",
            phone_number="+15551234567",
        )

        await provider.send_consent_request(
            target_contact="+15559876543",
            requester_name="Alice",
            target_name="Bob",
            scope="wellness_check",
            consent_url="https://consent.example.com/abc123",
        )

        call_args = mock_client.messages.create.call_args
        message_body = call_args[1]["body"]
        assert "https://consent.example.com/abc123" in message_body


class TestTwilioMessageFormatting:
    """Tests for TwilioMessageProvider message formatting."""

    def test_format_message_includes_requester(self):
        """Test message format includes requester name."""
        provider = TwilioMessageProvider()

        message = provider._format_message(
            requester_name="Alice",
            target_name="Bob",
            scope="wellness_check",
        )

        assert "Alice" in message

    def test_format_message_includes_scope(self):
        """Test message format includes scope."""
        provider = TwilioMessageProvider()

        message = provider._format_message(
            requester_name="Alice",
            target_name="Bob",
            scope="wellness_check",
        )

        assert "wellness_check" in message

    def test_format_message_includes_target_name(self):
        """Test message format includes target name."""
        provider = TwilioMessageProvider()

        message = provider._format_message(
            requester_name="Alice",
            target_name="Bob",
            scope="wellness_check",
        )

        assert "Bob" in message

    def test_format_message_handles_no_target_name(self):
        """Test message format handles missing target name."""
        provider = TwilioMessageProvider()

        message = provider._format_message(
            requester_name="Alice",
            target_name=None,
            scope="wellness_check",
        )

        # Should still include requester and scope
        assert "Alice" in message
        assert "wellness_check" in message
