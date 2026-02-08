"""Tests for consent web endpoints."""

from datetime import datetime, timedelta
from uuid import uuid4
from unittest.mock import AsyncMock, MagicMock

import pytest
from fastapi.testclient import TestClient

from consent_mcp.domain.entities import ConsentRequest
from consent_mcp.domain.value_objects import (
    ConsentActionResult,
    ContactInfo,
    ContactType,
    ConsentStatus,
)
from consent_mcp.domain.services import ConsentService
from consent_mcp.web.app import ConsentWebApp, create_app


@pytest.fixture
def mock_service():
    """Create a mock consent service."""
    return MagicMock(spec=ConsentService)


@pytest.fixture
def sample_consent_request():
    """Create a sample consent request for testing."""
    return ConsentRequest(
        id=uuid4(),
        requester=ContactInfo(
            contact_type=ContactType.EMAIL,
            contact_value="requester@example.com",
            name="Test Requester",
        ),
        target=ContactInfo(
            contact_type=ContactType.EMAIL,
            contact_value="target@example.com",
            name="Test User",
        ),
        scope="AI agent communication for customer support",
        status=ConsentStatus.PENDING,
        expires_at=datetime.utcnow() + timedelta(days=7),
    )


@pytest.fixture
def web_app(mock_service):
    """Create a test web app."""
    return ConsentWebApp(mock_service)


@pytest.fixture
def client(web_app):
    """Create a test client."""
    return TestClient(web_app.app)


class TestConsentPageDisplay:
    """Tests for GET /v1/consent/{token} endpoint."""

    def test_shows_consent_page_for_pending_request(
        self, client, mock_service, sample_consent_request
    ):
        """Pending requests should show the consent confirmation page."""
        mock_service.get_request_by_id = AsyncMock(return_value=sample_consent_request)

        response = client.get(f"/v1/consent/{sample_consent_request.id}")

        assert response.status_code == 200
        assert "Consent Request" in response.text
        assert "Test Requester" in response.text
        assert "customer support" in response.text
        assert "Grant Consent" in response.text
        assert "Decline" in response.text

    def test_shows_greeting_with_target_name(
        self, client, mock_service, sample_consent_request
    ):
        """Should greet the target by name if available."""
        mock_service.get_request_by_id = AsyncMock(return_value=sample_consent_request)

        response = client.get(f"/v1/consent/{sample_consent_request.id}")

        assert "Test User" in response.text

    def test_shows_already_responded_for_granted_request(
        self, client, mock_service, sample_consent_request
    ):
        """Already granted requests should show appropriate message."""
        sample_consent_request.status = ConsentStatus.GRANTED
        mock_service.get_request_by_id = AsyncMock(return_value=sample_consent_request)

        response = client.get(f"/v1/consent/{sample_consent_request.id}")

        assert response.status_code == 200
        assert "Already Responded" in response.text
        assert "granted" in response.text.lower()

    def test_shows_already_responded_for_revoked_request(
        self, client, mock_service, sample_consent_request
    ):
        """Already revoked requests should show appropriate message."""
        sample_consent_request.status = ConsentStatus.REVOKED
        mock_service.get_request_by_id = AsyncMock(return_value=sample_consent_request)

        response = client.get(f"/v1/consent/{sample_consent_request.id}")

        assert response.status_code == 200
        assert "Already Responded" in response.text

    def test_returns_404_for_unknown_token(self, client, mock_service):
        """Unknown tokens should return 404."""
        mock_service.get_request_by_id = AsyncMock(return_value=None)

        response = client.get(f"/v1/consent/{uuid4()}")

        assert response.status_code == 404

    def test_returns_400_for_invalid_token_format(self, client):
        """Invalid token formats should return 400."""
        response = client.get("/v1/consent/not-a-uuid")

        assert response.status_code == 400
        assert "Invalid consent token" in response.text


class TestGrantConsent:
    """Tests for POST /v1/consent/{token}/grant endpoint."""

    def test_grants_pending_request(
        self, client, mock_service, sample_consent_request
    ):
        """Should grant consent for pending requests."""
        mock_service.grant_consent = AsyncMock(
            return_value=ConsentActionResult(
                success=True,
                new_status=ConsentStatus.GRANTED,
                message="Consent granted",
            )
        )

        response = client.post(f"/v1/consent/{sample_consent_request.id}/grant")

        assert response.status_code == 200
        assert "Consent Granted" in response.text
        assert "Thank you" in response.text

    def test_returns_already_responded_for_granted_request(
        self, client, mock_service, sample_consent_request
    ):
        """Should not allow granting already granted requests."""
        mock_service.grant_consent = AsyncMock(
            return_value=ConsentActionResult(
                success=False,
                new_status=ConsentStatus.GRANTED,
                message="Request already granted",
            )
        )

        response = client.post(f"/v1/consent/{sample_consent_request.id}/grant")

        assert response.status_code == 200
        assert "Already Responded" in response.text

    def test_returns_404_for_unknown_token(self, client, mock_service):
        """Unknown tokens should return 404."""
        mock_service.grant_consent = AsyncMock(
            return_value=ConsentActionResult(
                success=False,
                new_status=None,
                message="Consent request not found",
            )
        )

        response = client.post(f"/v1/consent/{uuid4()}/grant")

        assert response.status_code == 404

    def test_returns_400_for_invalid_token_format(self, client):
        """Invalid token formats should return 400."""
        response = client.post("/v1/consent/not-a-uuid/grant")

        assert response.status_code == 400


class TestDenyConsent:
    """Tests for POST /v1/consent/{token}/deny endpoint."""

    def test_denies_pending_request(
        self, client, mock_service, sample_consent_request
    ):
        """Should deny consent for pending requests."""
        mock_service.deny_consent = AsyncMock(
            return_value=ConsentActionResult(
                success=True,
                new_status=ConsentStatus.REVOKED,
                message="Consent denied",
            )
        )

        response = client.post(f"/v1/consent/{sample_consent_request.id}/deny")

        assert response.status_code == 200
        assert "Consent Declined" in response.text

    def test_returns_already_responded_for_revoked_request(
        self, client, mock_service, sample_consent_request
    ):
        """Should not allow denying already revoked requests."""
        mock_service.deny_consent = AsyncMock(
            return_value=ConsentActionResult(
                success=False,
                new_status=ConsentStatus.REVOKED,
                message="Request already revoked",
            )
        )

        response = client.post(f"/v1/consent/{sample_consent_request.id}/deny")

        assert response.status_code == 200
        assert "Already Responded" in response.text

    def test_returns_404_for_unknown_token(self, client, mock_service):
        """Unknown tokens should return 404."""
        mock_service.deny_consent = AsyncMock(
            return_value=ConsentActionResult(
                success=False,
                new_status=None,
                message="Consent request not found",
            )
        )

        response = client.post(f"/v1/consent/{uuid4()}/deny")

        assert response.status_code == 404


class TestHealthCheck:
    """Tests for GET /health endpoint."""

    def test_returns_healthy_status(self, client):
        """Health check should return healthy status."""
        response = client.get("/health")

        assert response.status_code == 200
        assert response.json() == {"status": "healthy"}


class TestCreateAppFactory:
    """Tests for the create_app factory function."""

    def test_creates_fastapi_app(self, mock_service):
        """Factory should create a FastAPI application."""
        app = create_app(mock_service)

        assert app is not None
        assert app.title == "Consent Gateway"
