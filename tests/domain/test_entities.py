"""Tests for ConsentRequest domain entity."""

from datetime import datetime, timedelta, timezone

from consent_mcp.domain.entities import ConsentRequest
from consent_mcp.domain.value_objects import ConsentStatus


class TestConsentRequestIsActive:
    """Tests for ConsentRequest.is_active method."""

    def test_is_active_returns_true_for_granted_not_expired(
        self, sample_phone_requester, sample_phone_target
    ):
        """Test is_active returns True for granted, unexpired consent."""
        request = ConsentRequest(
            requester=sample_phone_requester,
            target=sample_phone_target,
            scope="wellness_check",
            status=ConsentStatus.GRANTED,
            expires_at=datetime.now(timezone.utc) + timedelta(days=30),
        )

        assert request.is_active() is True

    def test_is_active_returns_false_for_pending(self, sample_phone_requester, sample_phone_target):
        """Test is_active returns False for pending consent."""
        request = ConsentRequest(
            requester=sample_phone_requester,
            target=sample_phone_target,
            scope="wellness_check",
            status=ConsentStatus.PENDING,
            expires_at=datetime.now(timezone.utc) + timedelta(days=30),
        )

        assert request.is_active() is False

    def test_is_active_returns_false_for_expired(self, sample_phone_requester, sample_phone_target):
        """Test is_active returns False for expired consent."""
        request = ConsentRequest(
            requester=sample_phone_requester,
            target=sample_phone_target,
            scope="wellness_check",
            status=ConsentStatus.GRANTED,
            expires_at=datetime.now(timezone.utc) - timedelta(days=1),
        )

        assert request.is_active() is False

    def test_is_active_returns_false_for_revoked(self, sample_phone_requester, sample_phone_target):
        """Test is_active returns False for revoked consent."""
        request = ConsentRequest(
            requester=sample_phone_requester,
            target=sample_phone_target,
            scope="wellness_check",
            status=ConsentStatus.REVOKED,
            expires_at=datetime.now(timezone.utc) + timedelta(days=30),
        )

        assert request.is_active() is False


class TestConsentRequestStatusTransitions:
    """Tests for ConsentRequest status transition methods."""

    def test_grant_updates_status(self, sample_phone_requester, sample_phone_target):
        """Test grant() updates status to GRANTED."""
        request = ConsentRequest(
            requester=sample_phone_requester,
            target=sample_phone_target,
            scope="wellness_check",
            expires_at=datetime.now(timezone.utc) + timedelta(days=30),
        )

        granted = request.grant()

        assert granted.status == ConsentStatus.GRANTED
        assert granted.responded_at is not None

    def test_revoke_updates_status(self, sample_phone_requester, sample_phone_target):
        """Test revoke() updates status to REVOKED."""
        request = ConsentRequest(
            requester=sample_phone_requester,
            target=sample_phone_target,
            scope="wellness_check",
            status=ConsentStatus.GRANTED,
            expires_at=datetime.now(timezone.utc) + timedelta(days=30),
        )

        revoked = request.revoke()

        assert revoked.status == ConsentStatus.REVOKED
        assert revoked.responded_at is not None

    def test_expire_updates_status(self, sample_phone_requester, sample_phone_target):
        """Test expire() updates status to EXPIRED."""
        request = ConsentRequest(
            requester=sample_phone_requester,
            target=sample_phone_target,
            scope="wellness_check",
            status=ConsentStatus.GRANTED,
            expires_at=datetime.now(timezone.utc) + timedelta(days=30),
        )

        expired = request.expire()

        assert expired.status == ConsentStatus.EXPIRED


class TestConsentRequestCreation:
    """Tests for ConsentRequest entity creation."""

    def test_default_status_is_pending(self, sample_phone_requester, sample_phone_target):
        """Test that new ConsentRequest defaults to PENDING status."""
        request = ConsentRequest(
            requester=sample_phone_requester,
            target=sample_phone_target,
            scope="wellness_check",
            expires_at=datetime.now(timezone.utc) + timedelta(days=30),
        )

        assert request.status == ConsentStatus.PENDING

    def test_id_is_generated_automatically(self, sample_phone_requester, sample_phone_target):
        """Test that ConsentRequest generates a UUID automatically."""
        request = ConsentRequest(
            requester=sample_phone_requester,
            target=sample_phone_target,
            scope="wellness_check",
            expires_at=datetime.now(timezone.utc) + timedelta(days=30),
        )

        assert request.id is not None

    def test_created_at_is_set_automatically(self, sample_phone_requester, sample_phone_target):
        """Test that created_at is set automatically."""
        request = ConsentRequest(
            requester=sample_phone_requester,
            target=sample_phone_target,
            scope="wellness_check",
            expires_at=datetime.utcnow() + timedelta(days=30),
        )

        assert request.created_at is not None
