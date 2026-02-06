"""Test configuration and fixtures."""

import asyncio
from typing import AsyncGenerator, Generator
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

import pytest
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker

from consent_mcp.config import Settings
from consent_mcp.domain.entities import ConsentRequest
from consent_mcp.domain.value_objects import ContactInfo, ContactType, ConsentStatus
from consent_mcp.domain.providers import IMessageProvider, MessageDeliveryResult, ProviderType
from consent_mcp.domain.auth import IAuthProvider, AuthContext
from consent_mcp.domain.services import ConsentService
from consent_mcp.infrastructure.database.models import Base
from consent_mcp.infrastructure.database.repository import PostgresConsentRepository


# ============================================
# Event loop fixture
# ============================================
@pytest.fixture(scope="session")
def event_loop() -> Generator:
    """Create event loop for async tests."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


# ============================================
# Test settings
# ============================================
@pytest.fixture
def test_settings() -> Settings:
    """Create test settings."""
    return Settings(
        env="test",
        database_url="postgresql+asyncpg://consent_test:consent_test@localhost:5433/consent_test_db",
        auth_provider="none",
        api_keys="test_key:test_client",
    )


# ============================================
# Database fixtures
# ============================================
@pytest.fixture
async def async_engine(test_settings):
    """Create async engine for tests."""
    engine = create_async_engine(
        test_settings.database_url,
        echo=False,
    )
    
    # Create tables
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    yield engine
    
    # Drop tables
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    
    await engine.dispose()


@pytest.fixture
async def async_session(async_engine) -> AsyncGenerator[AsyncSession, None]:
    """Create async session for tests."""
    session_factory = async_sessionmaker(
        async_engine,
        class_=AsyncSession,
        expire_on_commit=False,
    )
    
    async with session_factory() as session:
        yield session
        await session.rollback()


@pytest.fixture
async def repository(async_session) -> PostgresConsentRepository:
    """Create repository for tests."""
    return PostgresConsentRepository(async_session)


# ============================================
# Mock providers
# ============================================
@pytest.fixture
def mock_sms_provider() -> IMessageProvider:
    """Create mock SMS provider."""
    provider = MagicMock(spec=IMessageProvider)
    provider.provider_type = ProviderType.SMS
    provider.provider_name = "mock_sms"
    provider.is_configured.return_value = True
    provider.validate_contact = AsyncMock(return_value=True)
    provider.send_consent_request = AsyncMock(
        return_value=MessageDeliveryResult(
            success=True,
            provider="mock_sms",
            message_id="mock_msg_123",
        )
    )
    return provider


@pytest.fixture
def mock_email_provider() -> IMessageProvider:
    """Create mock email provider."""
    provider = MagicMock(spec=IMessageProvider)
    provider.provider_type = ProviderType.EMAIL
    provider.provider_name = "mock_email"
    provider.is_configured.return_value = True
    provider.validate_contact = AsyncMock(return_value=True)
    provider.send_consent_request = AsyncMock(
        return_value=MessageDeliveryResult(
            success=True,
            provider="mock_email",
            message_id="mock_email_123",
        )
    )
    return provider


@pytest.fixture
def mock_auth_provider() -> IAuthProvider:
    """Create mock auth provider."""
    provider = MagicMock(spec=IAuthProvider)
    provider.provider_name = "mock_auth"
    provider.extract_credentials.return_value = {"api_key": "test_key"}
    provider.authenticate = AsyncMock(
        return_value=AuthContext(
            client_id="test_client",
            client_name="Test Client",
            scopes=["*"],
        )
    )
    return provider


# ============================================
# Service fixture
# ============================================
@pytest.fixture
async def consent_service(
    repository, mock_sms_provider, mock_email_provider
) -> ConsentService:
    """Create consent service with mocked providers."""
    return ConsentService(
        repository=repository,
        sms_provider=mock_sms_provider,
        email_provider=mock_email_provider,
    )


# ============================================
# Sample data fixtures
# ============================================
@pytest.fixture
def sample_phone_requester() -> ContactInfo:
    """Sample phone requester."""
    return ContactInfo(
        contact_type=ContactType.PHONE,
        contact_value="+15551234567",
        name="Alice",
    )


@pytest.fixture
def sample_phone_target() -> ContactInfo:
    """Sample phone target."""
    return ContactInfo(
        contact_type=ContactType.PHONE,
        contact_value="+15559876543",
        name="Bob",
    )


@pytest.fixture
def sample_email_requester() -> ContactInfo:
    """Sample email requester."""
    return ContactInfo(
        contact_type=ContactType.EMAIL,
        contact_value="alice@example.com",
        name="Alice",
    )


@pytest.fixture
def sample_email_target() -> ContactInfo:
    """Sample email target."""
    return ContactInfo(
        contact_type=ContactType.EMAIL,
        contact_value="bob@example.com",
        name="Bob",
    )
