"""Value objects for the consent domain."""

import re
from enum import Enum

from pydantic import BaseModel, EmailStr, field_validator, model_validator


class ContactType(str, Enum):
    """Type of contact method."""

    PHONE = "phone"
    EMAIL = "email"


class ConsentStatus(str, Enum):
    """Status of a consent request."""

    PENDING = "pending"
    GRANTED = "granted"
    REVOKED = "revoked"
    EXPIRED = "expired"


# E.164 phone number pattern
E164_PATTERN = re.compile(r"^\+[1-9]\d{1,14}$")


class ContactInfo(BaseModel):
    """
    Immutable value object representing contact information.
    
    Validates phone numbers are in E.164 format and emails are valid.
    """

    contact_type: ContactType
    contact_value: str
    name: str | None = None

    @model_validator(mode="after")
    def validate_contact_value(self) -> "ContactInfo":
        """Validate contact value matches the contact type."""
        if self.contact_type == ContactType.PHONE:
            if not E164_PATTERN.match(self.contact_value):
                raise ValueError(
                    f"Phone number must be in E.164 format (e.g., +15551234567), "
                    f"got: {self.contact_value}"
                )
        elif self.contact_type == ContactType.EMAIL:
            # Basic email validation
            if "@" not in self.contact_value or "." not in self.contact_value:
                raise ValueError(f"Invalid email address: {self.contact_value}")
        return self

    def __hash__(self) -> int:
        """Make ContactInfo hashable for use as dict keys."""
        return hash((self.contact_type, self.contact_value))

    def __eq__(self, other: object) -> bool:
        """Check equality based on type and value."""
        if not isinstance(other, ContactInfo):
            return False
        return (
            self.contact_type == other.contact_type
            and self.contact_value == other.contact_value
        )

    class Config:
        frozen = True  # Make immutable


def validate_phone(phone: str) -> str:
    """Validate and return phone number in E.164 format."""
    if not E164_PATTERN.match(phone):
        raise ValueError(
            f"Phone number must be in E.164 format (e.g., +15551234567), got: {phone}"
        )
    return phone


def validate_email(email: str) -> str:
    """Validate and return email address."""
    if "@" not in email or "." not in email:
        raise ValueError(f"Invalid email address: {email}")
    return email
