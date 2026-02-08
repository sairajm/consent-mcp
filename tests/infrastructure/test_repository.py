"""Tests for PostgresConsentRepository."""

from datetime import datetime, timedelta, timezone
from uuid import uuid4

import pytest

from consent_mcp.domain.entities import ConsentRequest
from consent_mcp.domain.repository import DuplicateRequestError, RequestNotFoundError
from consent_mcp.domain.value_objects import ConsentStatus


class TestRepositoryCreate:
    """Tests for PostgresConsentRepository.create method."""

    @pytest.mark.asyncio
    async def test_create_saves_consent_request(
        self, repository, sample_phone_requester, sample_phone_target
    ):
        """Test that create() saves a consent request."""
        request = ConsentRequest(
            requester=sample_phone_requester,
            target=sample_phone_target,
            scope="wellness_check",
            expires_at=datetime.now(timezone.utc) + timedelta(days=30),
        )

        saved = await repository.create(request)

        assert saved.id == request.id
        assert saved.status == ConsentStatus.PENDING

    @pytest.mark.asyncio
    async def test_create_raises_on_duplicate(
        self, repository, sample_phone_requester, sample_phone_target
    ):
        """Test that create() raises DuplicateRequestError for duplicates."""
        request1 = ConsentRequest(
            requester=sample_phone_requester,
            target=sample_phone_target,
            scope="wellness_check",
            expires_at=datetime.now(timezone.utc) + timedelta(days=30),
        )
        await repository.create(request1)

        # Try to create duplicate
        request2 = ConsentRequest(
            requester=sample_phone_requester,
            target=sample_phone_target,
            scope="wellness_check",  # Same scope
            expires_at=datetime.utcnow() + timedelta(days=60),
        )

        with pytest.raises(DuplicateRequestError):
            await repository.create(request2)


class TestRepositoryGetById:
    """Tests for PostgresConsentRepository.get_by_id method."""

    @pytest.mark.asyncio
    async def test_get_by_id_returns_request(
        self, repository, sample_phone_requester, sample_phone_target
    ):
        """Test that get_by_id() returns the correct request."""
        request = ConsentRequest(
            requester=sample_phone_requester,
            target=sample_phone_target,
            scope="wellness_check",
            expires_at=datetime.now(timezone.utc) + timedelta(days=30),
        )
        await repository.create(request)

        retrieved = await repository.get_by_id(request.id)

        assert retrieved is not None
        assert retrieved.id == request.id
        assert retrieved.scope == request.scope

    @pytest.mark.asyncio
    async def test_get_by_id_returns_none_for_missing(self, repository):
        """Test that get_by_id() returns None for missing ID."""
        retrieved = await repository.get_by_id(uuid4())
        assert retrieved is None


class TestRepositoryGetActiveConsent:
    """Tests for PostgresConsentRepository.get_active_consent method."""

    @pytest.mark.asyncio
    async def test_get_active_consent_returns_granted_unexpired(
        self, repository, sample_phone_requester, sample_phone_target
    ):
        """Test get_active_consent returns granted, unexpired consent."""
        request = ConsentRequest(
            requester=sample_phone_requester,
            target=sample_phone_target,
            scope="wellness_check",
            status=ConsentStatus.GRANTED,
            expires_at=datetime.now(timezone.utc) + timedelta(days=30),
        )
        await repository.create(request)

        active = await repository.get_active_consent(
            requester=sample_phone_requester,
            target=sample_phone_target,
        )

        assert active is not None
        assert active.id == request.id

    @pytest.mark.asyncio
    async def test_get_active_consent_ignores_pending(
        self, repository, sample_phone_requester, sample_phone_target
    ):
        """Test get_active_consent ignores pending requests."""
        request = ConsentRequest(
            requester=sample_phone_requester,
            target=sample_phone_target,
            scope="wellness_check",
            status=ConsentStatus.PENDING,
            expires_at=datetime.now(timezone.utc) + timedelta(days=30),
        )
        await repository.create(request)

        active = await repository.get_active_consent(
            requester=sample_phone_requester,
            target=sample_phone_target,
        )

        assert active is None

    @pytest.mark.asyncio
    async def test_get_active_consent_ignores_expired(
        self, repository, sample_phone_requester, sample_phone_target
    ):
        """Test get_active_consent ignores expired requests."""
        request = ConsentRequest(
            requester=sample_phone_requester,
            target=sample_phone_target,
            scope="wellness_check",
            status=ConsentStatus.GRANTED,
            expires_at=datetime.now(timezone.utc) - timedelta(days=1),  # Expired
        )
        await repository.create(request)

        active = await repository.get_active_consent(
            requester=sample_phone_requester,
            target=sample_phone_target,
        )

        assert active is None

    @pytest.mark.asyncio
    async def test_get_active_consent_ignores_revoked(
        self, repository, sample_phone_requester, sample_phone_target
    ):
        """Test get_active_consent ignores revoked requests."""
        request = ConsentRequest(
            requester=sample_phone_requester,
            target=sample_phone_target,
            scope="wellness_check",
            status=ConsentStatus.REVOKED,
            expires_at=datetime.now(timezone.utc) + timedelta(days=30),
        )
        await repository.create(request)

        active = await repository.get_active_consent(
            requester=sample_phone_requester,
            target=sample_phone_target,
        )

        assert active is None


class TestRepositoryUpdateStatus:
    """Tests for PostgresConsentRepository.update_status method."""

    @pytest.mark.asyncio
    async def test_update_status_updates_request(
        self, repository, sample_phone_requester, sample_phone_target
    ):
        """Test update_status updates the request status."""
        request = ConsentRequest(
            requester=sample_phone_requester,
            target=sample_phone_target,
            scope="wellness_check",
            expires_at=datetime.now(timezone.utc) + timedelta(days=30),
        )
        await repository.create(request)

        updated = await repository.update_status(request.id, ConsentStatus.GRANTED)

        assert updated.status == ConsentStatus.GRANTED
        assert updated.responded_at is not None

    @pytest.mark.asyncio
    async def test_update_status_raises_for_missing(self, repository):
        """Test update_status raises for missing request."""
        with pytest.raises(RequestNotFoundError):
            await repository.update_status(uuid4(), ConsentStatus.GRANTED)


class TestRepositoryFindMethods:
    """Tests for PostgresConsentRepository.find_by_* methods."""

    @pytest.mark.asyncio
    async def test_find_by_target_returns_matching_requests(
        self, repository, sample_phone_requester, sample_phone_target
    ):
        """Test find_by_target returns all requests for a target."""
        request = ConsentRequest(
            requester=sample_phone_requester,
            target=sample_phone_target,
            scope="wellness_check",
            expires_at=datetime.now(timezone.utc) + timedelta(days=30),
        )
        await repository.create(request)

        results = await repository.find_by_target(sample_phone_target)

        assert len(results) == 1
        assert results[0].id == request.id

    @pytest.mark.asyncio
    async def test_find_by_requester_returns_matching_requests(
        self, repository, sample_phone_requester, sample_phone_target
    ):
        """Test find_by_requester returns all requests from a requester."""
        request = ConsentRequest(
            requester=sample_phone_requester,
            target=sample_phone_target,
            scope="wellness_check",
            expires_at=datetime.now(timezone.utc) + timedelta(days=30),
        )
        await repository.create(request)

        results = await repository.find_by_requester(sample_phone_requester)

        assert len(results) == 1
        assert results[0].id == request.id

    @pytest.mark.asyncio
    async def test_find_by_target_returns_empty_for_no_matches(
        self, repository, sample_phone_target
    ):
        """Test find_by_target returns empty list when no matches."""
        results = await repository.find_by_target(sample_phone_target)
        assert results == []

    @pytest.mark.asyncio
    async def test_find_by_requester_returns_empty_for_no_matches(
        self, repository, sample_phone_requester
    ):
        """Test find_by_requester returns empty list when no matches."""
        results = await repository.find_by_requester(sample_phone_requester)
        assert results == []
