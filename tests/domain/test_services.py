"""Tests for ConsentService domain service."""

import pytest

from consent_mcp.domain.services import ConsentService


class TestConsentServiceRequestConsent:
    """Tests for ConsentService.request_consent method."""

    @pytest.mark.asyncio
    async def test_request_consent_sms_creates_pending_request(
        self, consent_service, sample_phone_requester, sample_phone_target, mock_sms_provider
    ):
        """Test that requesting consent via SMS creates a pending request."""
        result = await consent_service.request_consent(
            requester=sample_phone_requester,
            target=sample_phone_target,
            scope="wellness_check",
            expires_in_days=30,
        )

        assert result["status"] == "pending"
        assert result["request_id"] is not None
        assert "expires_at" in result
        
        # Verify SMS was sent
        mock_sms_provider.send_consent_request.assert_called_once()

    @pytest.mark.asyncio
    async def test_request_consent_email_creates_pending_request(
        self, consent_service, sample_email_requester, sample_email_target, mock_email_provider
    ):
        """Test that requesting consent via email creates a pending request."""
        result = await consent_service.request_consent(
            requester=sample_email_requester,
            target=sample_email_target,
            scope="appointment_reminder",
            expires_in_days=365,
        )

        assert result["status"] == "pending"
        assert result["request_id"] is not None
        
        # Verify email was sent
        mock_email_provider.send_consent_request.assert_called_once()

    @pytest.mark.asyncio
    async def test_request_consent_returns_existing_if_already_pending(
        self, consent_service, sample_phone_requester, sample_phone_target
    ):
        """Test that duplicate request returns existing pending request."""
        # First request
        result1 = await consent_service.request_consent(
            requester=sample_phone_requester,
            target=sample_phone_target,
            scope="wellness_check",
            expires_in_days=30,
        )

        # Second request for same requester/target/scope
        result2 = await consent_service.request_consent(
            requester=sample_phone_requester,
            target=sample_phone_target,
            scope="wellness_check",
            expires_in_days=30,
        )

        assert result2["status"] == "pending"
        assert result2["request_id"] == result1["request_id"]
        assert "already pending" in result2["message"].lower()


class TestConsentServiceCheckConsent:
    """Tests for ConsentService.check_consent method."""

    @pytest.mark.asyncio
    async def test_check_consent_returns_false_for_pending(
        self, consent_service, sample_phone_requester, sample_phone_target
    ):
        """Test that check_consent returns False for pending requests."""
        await consent_service.request_consent(
            requester=sample_phone_requester,
            target=sample_phone_target,
            scope="wellness_check",
            expires_in_days=30,
        )

        has_consent = await consent_service.check_consent(
            requester=sample_phone_requester,
            target=sample_phone_target,
        )

        assert has_consent is False

    @pytest.mark.asyncio
    async def test_check_consent_returns_false_when_no_request(
        self, consent_service, sample_phone_requester, sample_phone_target
    ):
        """Test that check_consent returns False when no request exists."""
        has_consent = await consent_service.check_consent(
            requester=sample_phone_requester,
            target=sample_phone_target,
        )

        assert has_consent is False


class TestConsentServiceSimulateResponse:
    """Tests for ConsentService.simulate_response method."""

    @pytest.mark.asyncio
    async def test_simulate_response_grants_consent(
        self, consent_service, sample_phone_requester, sample_phone_target
    ):
        """Test that simulate_response with YES grants consent."""
        # Create request
        await consent_service.request_consent(
            requester=sample_phone_requester,
            target=sample_phone_target,
            scope="wellness_check",
            expires_in_days=30,
        )

        # Simulate YES response
        result = await consent_service.simulate_response(
            target=sample_phone_target,
            requester_contact_value=sample_phone_requester.contact_value,
            response="YES",
        )

        assert result["success"] is True
        assert result["new_status"] == "granted"

        # Verify consent is now active
        has_consent = await consent_service.check_consent(
            requester=sample_phone_requester,
            target=sample_phone_target,
        )
        assert has_consent is True

    @pytest.mark.asyncio
    async def test_simulate_response_declines_consent(
        self, consent_service, sample_phone_requester, sample_phone_target
    ):
        """Test that simulate_response with NO declines consent."""
        # Create request
        await consent_service.request_consent(
            requester=sample_phone_requester,
            target=sample_phone_target,
            scope="wellness_check",
            expires_in_days=30,
        )

        # Simulate NO response
        result = await consent_service.simulate_response(
            target=sample_phone_target,
            requester_contact_value=sample_phone_requester.contact_value,
            response="NO",
        )

        assert result["success"] is True
        assert result["new_status"] == "revoked"

        # Verify consent is not active
        has_consent = await consent_service.check_consent(
            requester=sample_phone_requester,
            target=sample_phone_target,
        )
        assert has_consent is False

    @pytest.mark.asyncio
    async def test_simulate_response_fails_without_pending_request(
        self, consent_service, sample_phone_target
    ):
        """Test that simulate_response fails when no pending request exists."""
        result = await consent_service.simulate_response(
            target=sample_phone_target,
            requester_contact_value="+15550000000",
            response="YES",
        )

        assert result["success"] is False
        assert "not found" in result["message"].lower()
