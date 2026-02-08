"""Tests for ContactInfo and ConsentStatus value objects."""

import pytest

from consent_mcp.domain.value_objects import (
    ConsentStatus,
    ContactInfo,
    ContactType,
)


class TestContactType:
    """Tests for ContactType enum."""

    def test_phone_type_exists(self):
        """Test PHONE type exists."""
        assert ContactType.PHONE.value == "phone"

    def test_email_type_exists(self):
        """Test EMAIL type exists."""
        assert ContactType.EMAIL.value == "email"


class TestConsentStatus:
    """Tests for ConsentStatus enum."""

    def test_pending_status_exists(self):
        """Test PENDING status exists."""
        assert ConsentStatus.PENDING.value == "pending"

    def test_granted_status_exists(self):
        """Test GRANTED status exists."""
        assert ConsentStatus.GRANTED.value == "granted"

    def test_revoked_status_exists(self):
        """Test REVOKED status exists."""
        assert ConsentStatus.REVOKED.value == "revoked"

    def test_expired_status_exists(self):
        """Test EXPIRED status exists."""
        assert ConsentStatus.EXPIRED.value == "expired"


class TestContactInfoPhoneValidation:
    """Tests for ContactInfo phone number validation."""

    def test_valid_e164_phone_number(self):
        """Test valid E.164 phone numbers are accepted."""
        contact = ContactInfo(
            contact_type=ContactType.PHONE,
            contact_value="+15551234567",
            name="Test User",
        )
        assert contact.contact_value == "+15551234567"

    def test_valid_international_phone_number(self):
        """Test valid international phone numbers are accepted."""
        contact = ContactInfo(
            contact_type=ContactType.PHONE,
            contact_value="+447911123456",
            name="UK User",
        )
        assert contact.contact_value == "+447911123456"

    def test_invalid_phone_without_plus(self):
        """Test phone numbers without + prefix are rejected."""
        with pytest.raises(ValueError, match="E.164"):
            ContactInfo(
                contact_type=ContactType.PHONE,
                contact_value="15551234567",
                name="Test User",
            )

    def test_invalid_phone_too_short(self):
        """Test phone numbers that are too short are rejected."""
        with pytest.raises(ValueError, match="E.164"):
            ContactInfo(
                contact_type=ContactType.PHONE,
                contact_value="+1",
                name="Test User",
            )

    def test_invalid_phone_with_letters(self):
        """Test phone numbers with letters are rejected."""
        with pytest.raises(ValueError, match="E.164"):
            ContactInfo(
                contact_type=ContactType.PHONE,
                contact_value="+1555CALL",
                name="Test User",
            )


class TestContactInfoEmailValidation:
    """Tests for ContactInfo email validation."""

    def test_valid_email(self):
        """Test valid email addresses are accepted."""
        contact = ContactInfo(
            contact_type=ContactType.EMAIL,
            contact_value="user@example.com",
            name="Test User",
        )
        assert contact.contact_value == "user@example.com"

    def test_valid_email_with_subdomain(self):
        """Test email with subdomain is accepted."""
        contact = ContactInfo(
            contact_type=ContactType.EMAIL,
            contact_value="user@mail.example.com",
            name="Test User",
        )
        assert contact.contact_value == "user@mail.example.com"

    def test_invalid_email_no_at(self):
        """Test email without @ is rejected."""
        with pytest.raises(ValueError, match="email"):
            ContactInfo(
                contact_type=ContactType.EMAIL,
                contact_value="userexample.com",
                name="Test User",
            )

    def test_invalid_email_no_domain(self):
        """Test email without domain is rejected."""
        with pytest.raises(ValueError, match="email"):
            ContactInfo(
                contact_type=ContactType.EMAIL,
                contact_value="user@",
                name="Test User",
            )


class TestContactInfoEquality:
    """Tests for ContactInfo equality and hashing."""

    def test_same_values_are_equal(self):
        """Test ContactInfo with same values are equal."""
        contact1 = ContactInfo(
            contact_type=ContactType.PHONE,
            contact_value="+15551234567",
            name="Test User",
        )
        contact2 = ContactInfo(
            contact_type=ContactType.PHONE,
            contact_value="+15551234567",
            name="Test User",
        )
        assert contact1 == contact2

    def test_different_values_are_not_equal(self):
        """Test ContactInfo with different values are not equal."""
        contact1 = ContactInfo(
            contact_type=ContactType.PHONE,
            contact_value="+15551234567",
            name="Test User",
        )
        contact2 = ContactInfo(
            contact_type=ContactType.PHONE,
            contact_value="+15559876543",
            name="Test User",
        )
        assert contact1 != contact2

    def test_optional_name_field(self):
        """Test name field is optional."""
        contact = ContactInfo(
            contact_type=ContactType.PHONE,
            contact_value="+15551234567",
        )
        assert contact.name is None
